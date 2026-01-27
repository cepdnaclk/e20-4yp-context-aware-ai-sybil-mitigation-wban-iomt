from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from state import NodeState, update_state


CSV_COLUMNS = [
    "run_id",
    "scenario_id",
    "ts_gateway",
    "node_id",
    "boot_id",
    "seq",
    "msg_type",
    "payload_len",
    "iat",
    "seq_gap",
    "seq_reset_flag",
    "dup_seq_flag",
    "out_of_order_flag",
    "first_packet_flag",
    "boot_change_flag",
]


@dataclass
class RunConfig:
    run_id: int
    scenario_id: str
    description: str
    duration_s: int
    listen_ip: str
    listen_port: int
    output_root: str


def load_run_config(manifest_path: Path) -> Tuple[RunConfig, dict]:
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    gateway = manifest.get("gateway", {})
    cfg = RunConfig(
        run_id=int(manifest["run_id"]),
        scenario_id=str(manifest["scenario_id"]),
        description=str(manifest.get("description", "")),
        duration_s=int(manifest.get("duration_s", 0)),
        listen_ip=str(gateway.get("listen_ip", "0.0.0.0")),
        listen_port=int(gateway.get("listen_port", 5005)),
        output_root=str(gateway.get("output_root", "experiments/outputs")),
    )
    if cfg.duration_s <= 0:
        raise ValueError("duration_s must be a positive integer")
    return cfg, manifest


def run_output_dir(output_root: str, run_id: int) -> Path:
    return Path(output_root) / f"run_{run_id:04d}"


def parse_payload(payload_bytes: bytes) -> Optional[Tuple[str, int, int, str]]:
    """
    Parse payload: node_id,boot_id,seq,msg_type

    Returns None if invalid.
    """
    try:
        text = payload_bytes.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None

    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        return None

    node_id = parts[0]
    msg_type = parts[3]
    if not node_id or not msg_type:
        return None

    try:
        boot_id = int(parts[1])
        seq = int(parts[2])
    except ValueError:
        return None

    # basic bounds sanity
    if boot_id < 0 or boot_id > 65535:
        return None
    if seq < 0 or seq > 0xFFFFFFFF:
        return None

    return node_id, boot_id, seq, msg_type


def main() -> int:
    parser = argparse.ArgumentParser(description="WBAN Gateway Collector (Phase A)")
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to run manifest JSON (e.g., experiments/runs/S0_NORMAL/run_0001.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing run output directory if it exists.",
    )
    parser.add_argument(
        "--flush-every",
        type=int,
        default=50,
        help="Flush CSV file every N rows (default: 50).",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    cfg, manifest = load_run_config(manifest_path)

    out_dir = run_output_dir(cfg.output_root, cfg.run_id).resolve()
    if out_dir.exists():
        if not args.force:
            print(
                f"[ERROR] Output directory already exists: {out_dir}\n"
                f"        Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy manifest for traceability
    with (out_dir / "run.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    csv_path = out_dir / "udp_packets.csv"
    log_path = out_dir / "collector.log"

    # Stats
    total_packets = 0
    parsed_packets = 0
    parse_errors = 0
    per_node_counts: Dict[str, int] = {}
    seq_resets = 0
    out_of_orders = 0
    duplicates = 0
    boot_changes = 0

    states: Dict[str, NodeState] = {}

    # UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((cfg.listen_ip, cfg.listen_port))
    sock.settimeout(0.5)  # allow periodic time checks

    start_ts = time.time()
    end_ts = start_ts + cfg.duration_s

    with csv_path.open("w", newline="", encoding="utf-8") as csvfile, log_path.open(
        "w", encoding="utf-8"
    ) as logfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        logfile.write(f"run_id={cfg.run_id}\n")
        logfile.write(f"scenario_id={cfg.scenario_id}\n")
        logfile.write(f"listen={cfg.listen_ip}:{cfg.listen_port}\n")
        logfile.write(f"duration_s={cfg.duration_s}\n")
        logfile.write(f"started_at={start_ts}\n")

        print(
            f"[INFO] Collector started: {cfg.listen_ip}:{cfg.listen_port} "
            f"(run_id={cfg.run_id}, scenario_id={cfg.scenario_id}, duration={cfg.duration_s}s)"
        )

        rows_since_flush = 0

        try:
            while time.time() < end_ts:
                try:
                    payload, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue

                total_packets += 1
                ts_gateway = time.time()
                payload_len = len(payload)

                parsed = parse_payload(payload)
                if parsed is None:
                    parse_errors += 1
                    logfile.write(
                        f"[PARSE_ERROR] ts={ts_gateway} from={addr} len={payload_len}\n"
                    )
                    continue

                node_id, boot_id, seq, msg_type = parsed
                parsed_packets += 1
                per_node_counts[node_id] = per_node_counts.get(node_id, 0) + 1

                (
                    iat,
                    seq_gap,
                    seq_reset_flag,
                    dup_seq_flag,
                    out_of_order_flag,
                    first_packet_flag,
                    boot_change_flag,
                ) = update_state(
                    states,
                    node_id=node_id,
                    boot_id=boot_id,
                    seq=seq,
                    ts_gateway=ts_gateway,
                )

                if seq_reset_flag:
                    seq_resets += 1
                if out_of_order_flag:
                    out_of_orders += 1
                if dup_seq_flag:
                    duplicates += 1
                if boot_change_flag:
                    boot_changes += 1

                row = {
                    "run_id": cfg.run_id,
                    "scenario_id": cfg.scenario_id,
                    "ts_gateway": f"{ts_gateway:.6f}",
                    "node_id": node_id,
                    "boot_id": boot_id,
                    "seq": seq,
                    "msg_type": msg_type,
                    "payload_len": payload_len,
                    "iat": f"{iat:.6f}" if iat >= 0 else -1,
                    "seq_gap": seq_gap if seq_gap >= 0 else -1,
                    "seq_reset_flag": seq_reset_flag,
                    "dup_seq_flag": dup_seq_flag,
                    "out_of_order_flag": out_of_order_flag,
                    "first_packet_flag": first_packet_flag,
                    "boot_change_flag": boot_change_flag,
                }

                writer.writerow(row)
                rows_since_flush += 1

                if rows_since_flush >= args.flush_every:
                    csvfile.flush()
                    os.fsync(csvfile.fileno())
                    rows_since_flush = 0

        except KeyboardInterrupt:
            print("[INFO] Interrupted by user. Finalizing outputs...")

        # Final flush
        csvfile.flush()
        os.fsync(csvfile.fileno())

        logfile.write(f"ended_at={time.time()}\n")
        logfile.write(f"total_packets={total_packets}\n")
        logfile.write(f"parsed_packets={parsed_packets}\n")
        logfile.write(f"parse_errors={parse_errors}\n")
        logfile.write(f"seq_resets={seq_resets}\n")
        logfile.write(f"out_of_orders={out_of_orders}\n")
        logfile.write(f"duplicates={duplicates}\n")
        logfile.write(f"boot_changes={boot_changes}\n")
        for nid, cnt in sorted(per_node_counts.items()):
            logfile.write(f"node_packets[{nid}]={cnt}\n")

    sock.close()

    # Summary to console
    print("\n[SUMMARY]")
    print(f"  Output dir      : {out_dir}")
    print(f"  UDP CSV         : {csv_path}")
    print(f"  Total packets   : {total_packets}")
    print(f"  Parsed packets  : {parsed_packets}")
    print(f"  Parse errors    : {parse_errors}")
    print(f"  Seq resets      : {seq_resets}")
    print(f"  Out-of-order    : {out_of_orders}")
    print(f"  Duplicates      : {duplicates}")
    print(f"  Boot changes    : {boot_changes}")
    if per_node_counts:
        print("  Packets per node:")
        for nid, cnt in sorted(per_node_counts.items()):
            print(f"    - {nid}: {cnt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
