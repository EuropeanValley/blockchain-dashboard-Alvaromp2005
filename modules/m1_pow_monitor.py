"""Proof of Work monitor module."""

import pandas as pd
import plotly.express as px
import streamlit as st

from api.blockchain_client import get_latest_blockstream_block, get_recent_blocks
from modules.bitcoin_utils import (
    bits_to_difficulty,
    bits_to_target,
    block_intervals,
    block_hash_meets_target,
    estimate_hashrate,
    format_hashrate,
    format_large_number,
    format_timestamp,
    leading_zero_bits,
    target_to_padded_hex,
)


@st.cache_data(ttl=60)
def load_pow_data(block_count: int) -> tuple[dict, list[dict]]:
    """Load latest mining data with a short cache for automatic refreshes."""
    return get_latest_blockstream_block(), get_recent_blocks(block_count)


def render() -> None:
    """Render the M1 panel."""
    st.header("M1 - Proof of Work Monitor")
    st.caption("Live Bitcoin mining snapshot. Data is cached for 60 seconds.")

    block_count = st.slider("Blocks used for timing distribution", 20, 120, 50, step=10, key="m1_blocks")

    with st.spinner("Fetching live mining data..."):
        try:
            block, recent_blocks = load_pow_data(block_count)
            intervals = block_intervals(recent_blocks)
            df = pd.DataFrame(intervals)

            target = bits_to_target(block.get("bits"))
            difficulty = block.get("difficulty") or bits_to_difficulty(block.get("bits"))
            average_seconds = df["interval_seconds"].mean() if not df.empty else None
            hash_rate = estimate_hashrate(difficulty, average_seconds)
            is_valid_pow = block_hash_meets_target(block.get("id"), target)
            target_hex = target_to_padded_hex(target)
            target_zero_bits = leading_zero_bits(target_hex)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Height", format_large_number(block.get("height")))
            col2.metric("Difficulty", format_large_number(difficulty))
            col3.metric("Avg block time", f"{average_seconds / 60:,.2f} min" if average_seconds else "N/A")
            col4.metric("Estimated hash rate", format_hashrate(hash_rate))

            st.subheader("256-bit target threshold")
            st.write(f"Current block hash: `{block.get('id')}`")
            st.write(f"Target: `{target_hex}`")
            st.progress(min(target_zero_bits / 256, 1.0), text=f"Target starts with {target_zero_bits} leading zero bits")
            if is_valid_pow:
                st.success("The latest block hash is below the target threshold.")
            else:
                st.warning("The proof-of-work threshold could not be verified.")

            detail1, detail2, detail3 = st.columns(3)
            detail1.write(f"**UTC time:** {format_timestamp(block.get('timestamp'))}")
            detail1.write(f"**Bits:** `{block.get('bits'):08x}`")
            detail2.write(f"**Nonce:** {format_large_number(block.get('nonce'))}")
            detail2.write(f"**Transactions:** {format_large_number(block.get('tx_count'))}")
            detail3.write(f"**Hash leading zero bits:** {leading_zero_bits(block.get('id'))}")
            detail3.write("**Expected interval model:** exponential")

            if not df.empty:
                st.subheader("Time between recent blocks")
                fig = px.histogram(
                    df,
                    x="interval_minutes",
                    nbins=20,
                    title="Distribution of inter-block times",
                    labels={"interval_minutes": "Minutes between blocks", "count": "Number of blocks"},
                )
                st.plotly_chart(fig, width="stretch")
                st.write(
                    "Bitcoin mining attempts are memoryless, so an exponential distribution is the expected baseline; "
                    "short and long gaps are normal even when the long-term average targets 10 minutes."
                )

                with st.expander("Recent block intervals"):
                    st.dataframe(df, width="stretch")
        except Exception as exc:
            st.error(f"Error fetching data: {exc}")
