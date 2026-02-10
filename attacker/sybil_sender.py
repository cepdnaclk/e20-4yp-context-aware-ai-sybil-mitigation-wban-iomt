#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import socket
import sys
import time
from pathlib import Path


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sybil UDP sender (Phase A)")
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument(
        "--gateway-ip",
        default=None,
        help="Override gateway IP (default: auto-detect local default route target is not possible; use this if needed).",
    )
    parser.add_argument(
        "--gateway-port", type=int, default=None, help="Override gateway port"
    )
    parser.add_argument(
        "--duration-s",
        type=int,
        default=None,
        help="Override attack duration (default: manifest duration_s)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    m = load_manifest(manifest_path)

    attacker = m.get("attacker", {})
    if not attacker.get("enabled", False):
        print("[ERROR] attacker.enabled is false in manifest", file=sys.stderr)
        return 1

    gateway = m.get("gateway", {})
    gateway_ip = args.gateway_ip  # recommended to pass explicitly
    gateway_port = args.gateway_port or int(gateway.get("listen_port", 5005))

    if not gateway_ip:
        print(
            "[ERROR] gateway IP not provided.\n"
            "        Use --gateway-ip <your_laptop_ip> (e.g., 192.168.8.166).",
            file=sys.stderr,
        )
        return 1

    scenario_id = str(m.get("scenario_id", "UNKNOWN"))
    run_id = int(m.get("run_id", -1))
    duration_s = int(args.duration_s or m.get("duration_s", 300))

    target_node_id = str(attacker.get("target_node_id", "ecg_01"))
    msg_type = str(attacker.get("msg_type", "ECG"))
    pps = float(attacker.get("attack_rate_pps", 2))
    if pps <= 0:
        print("[ERROR] attack_rate_pps must be > 0", file=sys.stderr)
        return 1
    period_s = 1.0 / pps

    start_delay_s = float(attacker.get("start_delay_s", 0))

    # Sybil boot_id: attacker-controlled and stable during run (realistic “single device”)
    boot_id = random.randint(0, 65535)
    seq = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("[INFO] Sybil sender starting")
    print(f"  run_id           : {run_id}")
    print(f"  scenario_id      : {scenario_id}")
    print(f"  gateway          : {gateway_ip}:{gateway_port}")
    print(f"  clones node_id   : {target_node_id}")
    print(f"  msg_type         : {msg_type}")
    print(f"  attack_rate_pps  : {pps} (period {period_s:.3f}s)")
    print(f"  start_delay_s    : {start_delay_s}")
    print(f"  duration_s       : {duration_s}")
    print(f"  attacker boot_id : {boot_id}")

    if start_delay_s > 0:
        time.sleep(start_delay_s)

    start = time.time()
    end = start + duration_s
    next_send = time.time()

    sent = 0
    try:
        while time.time() < end:
            now = time.time()
            if now < next_send:
                time.sleep(min(0.01, next_send - now))
                continue

            payload = f"{target_node_id},{boot_id},{seq},{msg_type}".encode("utf-8")

            sock.sendto(payload, (gateway_ip, gateway_port))
            sent += 1
            seq += 1

            # schedule next send
            next_send += period_s

            if sent % int(max(1, pps * 5)) == 0:
                print(f"[TX] sent={sent} last_seq={seq-1}")

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")

    print(f"[SUMMARY] packets_sent={sent}")
    sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
