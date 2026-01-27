# Phase A Dataset Schema (S0_NORMAL)

This document describes the data schema for Phase A of the project,
which focuses on normal (non-Sybil) network traffic in a WBAN/IoMT system.

---

## UDP Payload Format (Node → Gateway)

Each sensor node transmits a single UDP message per packet using the
following comma-separated format:
```
node_id,boot_id,seq,msg_type
```

### Example Payload
```
ecg_01,41237,1024,ECG
```
---

### Payload Fields

| Field Name | Type | Description |
|-----------|------|-------------|
| node_id | string | Claimed identity of the node |
| boot_id | uint16 | Random value generated at boot to distinguish reboots |
| seq | uint32 | Monotonically increasing sequence counter |
| msg_type | string | Logical message category (e.g., ECG, EEG) |

The payload contains no timestamps, labels, or radio metrics. All payload
fields are considered untrusted.

---

## Gateway-Collected Fields (Per Packet)

| Field Name | Type | Description |
|-----------|------|-------------|
| run_id | int | Unique identifier for the experiment run |
| scenario_id | string | Scenario label (e.g., S0_NORMAL) |
| ts_gateway | float | Packet arrival timestamp at the gateway (seconds) |
| payload_len | int | UDP payload length in bytes |

---

## Gateway-Derived Per-Identity Fields

These fields are computed by the gateway using per-node state.

| Field Name | Type | Description |
|-----------|------|-------------|
| iat | float | Inter-arrival time between consecutive packets from the same node |
| seq_gap | int | Difference between current and previous sequence numbers |
| seq_reset_flag | bool | Indicates a detected sequence reset |
| dup_seq_flag | bool | Indicates a duplicated sequence number |
| out_of_order_flag | bool | Indicates packets arriving out of sequence |
| first_packet_flag | bool | Indicates first packet observed for a node in a run |
| boot_change_flag | bool | Indicates a change in boot identifier for the same node |

---

## Sniffer-Derived Radio Fields

These fields are extracted from monitor-mode Wi-Fi captures and represent
receiver-side radio observations.

| Field Name | Type | Description |
|-----------|------|-------------|
| ts_sniffer | float | Timestamp of frame capture at the sniffer |
| src_mac | string | Transmitter MAC address observed at the 802.11 layer |
| rssi_dbm | int | Receiver-measured signal strength (dBm) |

---

## Notes

- Gateway-side timestamps and derived features are considered authoritative.
- Node-reported values are treated as untrusted.
- No ground-truth labels are included in the payload or packet logs.
- Higher-level features (e.g., window-based statistics) are computed offline.