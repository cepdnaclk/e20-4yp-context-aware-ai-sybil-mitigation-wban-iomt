#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./parse_rssi.sh <pcap_in> <csv_out>
#
# Output columns (no header by default): ts_sniffer,src_mac,rssi_dbm
#
# Example:
#   ./parse_rssi.sh experiments/outputs/run_0001/sniff.pcap experiments/outputs/run_0001/sniffer_frames.csv

PCAP_IN="${1:-}"
CSV_OUT="${2:-}"

if [[ -z "$PCAP_IN" || -z "$CSV_OUT" ]]; then
  echo "Usage: $0 <pcap_in> <csv_out>" >&2
  exit 1
fi

if [[ ! -f "$PCAP_IN" ]]; then
  echo "[ERROR] PCAP not found: $PCAP_IN" >&2
  exit 2
fi

mkdir -p "$(dirname "$CSV_OUT")"

echo "[INFO] Extracting RSSI from PCAP"
echo "  pcap_in : $PCAP_IN"
echo "  csv_out : $CSV_OUT"

# We want:
# - frame.time_epoch           -> ts_sniffer
# - wlan.sa                    -> src_mac (802.11 source address)
# - radiotap.dbm_antsignal     -> rssi_dbm (receiver-side signal)
#
# Note:
# Some frames might not have wlan.sa or radiotap.dbm_antsignal; we drop those via awk.
tshark -r "$PCAP_IN" \
  -T fields -E separator=, -E quote=d -E occurrence=f \
  -e frame.time_epoch \
  -e wlan.sa \
  -e radiotap.dbm_antsignal \
  2>/dev/null \
| awk -F, 'NF==3 && $2!="" && $3!="" {print}' > "$CSV_OUT"

# Add header (recommended)
TMP="${CSV_OUT}.tmp"
{
  echo "ts_sniffer,src_mac,rssi_dbm"
  cat "$CSV_OUT"
} > "$TMP"
mv "$TMP" "$CSV_OUT"

echo "[INFO] RSSI CSV written: $(wc -l < "$CSV_OUT") lines"
