from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class NodeState:
    """Per-node state maintained at the gateway."""
    seen: bool = False
    last_ts: float = -1.0
    last_seq: int = -1
    last_boot_id: int = -1


def update_state(
    states: Dict[str, NodeState],
    *,
    node_id: str,
    boot_id: int,
    seq: int,
    ts_gateway: float,
) -> Tuple[float, int, int, int, int, int, int]:
    """
    Update per-node state and compute derived fields.

    Returns:
        iat (float): inter-arrival time in seconds (or -1 if first packet)
        seq_gap (int): seq - last_seq (or -1 if first packet)
        seq_reset_flag (0/1)
        dup_seq_flag (0/1)
        out_of_order_flag (0/1)
        first_packet_flag (0/1)
        boot_change_flag (0/1)
    """
    st = states.get(node_id)
    if st is None:
        st = NodeState()
        states[node_id] = st

    # First time we've seen this node_id during this run
    if not st.seen:
        first_packet_flag = 1
        iat = -1.0
        seq_gap = -1
        seq_reset_flag = 0
        dup_seq_flag = 0
        out_of_order_flag = 0
        boot_change_flag = 0

        st.seen = True
        st.last_ts = ts_gateway
        st.last_seq = seq
        st.last_boot_id = boot_id
        return (
            iat,
            seq_gap,
            seq_reset_flag,
            dup_seq_flag,
            out_of_order_flag,
            first_packet_flag,
            boot_change_flag,
        )

    # Not the first packet
    first_packet_flag = 0
    iat = ts_gateway - st.last_ts if st.last_ts >= 0 else -1.0
    seq_gap = seq - st.last_seq if st.last_seq >= 0 else -1

    dup_seq_flag = 1 if seq == st.last_seq else 0
    boot_change_flag = 1 if (st.last_boot_id >= 0 and boot_id != st.last_boot_id) else 0

    # Distinguish reset vs out-of-order using boot_id when possible
    if st.last_seq >= 0 and seq < st.last_seq:
        if boot_change_flag == 1:
            seq_reset_flag = 1
            out_of_order_flag = 0
        else:
            # Same boot_id but seq went backwards: treat as out-of-order
            seq_reset_flag = 0
            out_of_order_flag = 1
    else:
        seq_reset_flag = 0
        out_of_order_flag = 0

    # Update state
    st.last_ts = ts_gateway
    st.last_seq = seq
    st.last_boot_id = boot_id

    return (
        iat,
        seq_gap,
        seq_reset_flag,
        dup_seq_flag,
        out_of_order_flag,
        first_packet_flag,
        boot_change_flag,
    )
