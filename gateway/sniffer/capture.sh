#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./capture.sh <iface> <duration_s> <pcap_out>
#
# Example:
#   ./capture.sh wlp8s0f4u1mon 300 experiments/outputs/run_0001/sniff.pcap

IFACE="${1:-}"
DURATION="${2:-}"
PCAP_OUT="${3:-}"

if [[ -z "$IFACE" || -z "$DURATION" || -z "$PCAP_OUT" ]]; then
  echo "Usage: $0 <iface> <duration_s> <pcap_out>" >&2
  exit 1
fi

mkdir -p "$(dirname "$PCAP_OUT")"

echo "[INFO] Starting capture"
echo "  iface     : $IFACE"
echo "  duration  : ${DURATION}s"
echo "  pcap_out  : $PCAP_OUT"

# -I: monitor mode capture (expects IFACE is already monitor type)
# -s 0: capture full packet
# -w: write pcap
# timeout: stop after duration
sudo timeout "${DURATION}" tcpdump -I -i "${IFACE}" -s 0 -w "${PCAP_OUT}" 2>/dev/null || true

if [[ -f "$PCAP_OUT" ]]; then
  echo "[INFO] Capture complete: $(du -h "$PCAP_OUT" | awk '{print $1}')"
else
  echo "[WARN] PCAP was not created (check permissions / interface)" >&2
  exit 2
fi
