"""Block header analyzer module."""

import streamlit as st

from api.blockchain_client import get_block_hash_by_height, get_block_header, get_blockstream_block, get_tip_height
from modules.bitcoin_utils import (
    bits_to_target,
    block_hash_meets_target,
    format_large_number,
    format_timestamp,
    hash_header,
    leading_zero_bits,
    parse_block_header,
    target_to_padded_hex,
)


def render() -> None:
    """Render the M2 panel."""
    st.header("M2 - Block Header Analyzer")
    st.caption("Parse the real 80-byte block header and verify SHA256(SHA256(header)) locally.")

    block_hash = st.text_input(
        "Block hash (leave empty to use the latest block)",
        placeholder="000000000000...",
        key="m2_hash",
    )

    if st.button("Analyze block header", key="m2_lookup"):
        with st.spinner("Fetching data..."):
            try:
                selected_hash = block_hash.strip()
                if not selected_hash:
                    selected_hash = get_block_hash_by_height(get_tip_height())

                block = get_blockstream_block(selected_hash)
                header_hex = get_block_header(selected_hash)
                parsed = parse_block_header(header_hex)
                computed_hash = hash_header(header_hex)
                target = bits_to_target(parsed["bits"])
                is_valid_pow = block_hash_meets_target(computed_hash, target)

                st.success("Block found")
                st.subheader("80-byte header")
                st.code(header_hex)
                st.write(f"Header length: **{len(bytes.fromhex(header_hex))} bytes**")

                st.subheader("Six block header fields")
                header_fields = {
                    "Version": parsed["version"],
                    "Previous hash": parsed["previous_hash"],
                    "Merkle root": parsed["merkle_root"],
                    "Timestamp": format_timestamp(parsed["timestamp"]),
                    "Bits": parsed["bits_hex"],
                    "Nonce": parsed["nonce"],
                }
                for label, value in header_fields.items():
                    st.write(f"**{label}:** {value}")

                st.subheader("Local hashlib verification")
                col1, col2, col3 = st.columns(3)
                col1.metric("Computed hash matches API", "Yes" if computed_hash == selected_hash else "No")
                col2.metric("Leading zero bits", leading_zero_bits(computed_hash))
                col3.metric("Tx count", format_large_number(block.get("tx_count")))

                st.write(f"Computed double SHA-256 hash: `{computed_hash}`")
                st.write(f"API block hash: `{selected_hash}`")
                st.write(f"Target from bits: `{target_to_padded_hex(target)}`")
                if is_valid_pow:
                    st.success("Verification passed: double SHA-256(header) is below the target.")
                else:
                    st.warning("Verification failed or could not be confirmed.")

                with st.expander("Raw block data"):
                    st.json(block)
            except Exception as exc:
                st.error(f"Error fetching block: {exc}")
    else:
        st.info("Click Analyze block header to inspect the latest block, or paste a specific block hash.")
