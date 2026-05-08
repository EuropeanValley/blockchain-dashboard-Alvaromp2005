"""Optional M5: Merkle proof verifier."""

import pandas as pd
import streamlit as st

from api.blockchain_client import get_block_hash_by_height, get_block_header, get_block_txids, get_tip_height
from modules.bitcoin_utils import merkle_proof, merkle_root_from_txids, parse_block_header, verify_merkle_proof


@st.cache_data(ttl=600)
def load_merkle_data(height: int) -> tuple[str, str, list[str]]:
    """Load block hash, header Merkle root and txids for a height."""
    block_hash = get_block_hash_by_height(height)
    header = parse_block_header(get_block_header(block_hash))
    return block_hash, header["merkle_root"], get_block_txids(block_hash)


def render() -> None:
    """Render the M5 panel."""
    st.header("M5 - Merkle Proof Verifier")
    st.caption("Pick a transaction and verify its Merkle proof step by step.")

    try:
        tip_height = get_tip_height()
        default_height = max(0, tip_height - 6)
        height = st.number_input("Block height", min_value=0, max_value=tip_height, value=default_height, step=1)

        with st.spinner("Loading txids and header..."):
            block_hash, header_root, txids = load_merkle_data(int(height))

        tx_index = st.number_input(
            "Transaction index",
            min_value=0,
            max_value=max(0, len(txids) - 1),
            value=0,
            step=1,
        )
        selected_txid = txids[int(tx_index)]
        proof = merkle_proof(txids, int(tx_index))
        computed_root, steps = verify_merkle_proof(selected_txid, proof)
        full_tree_root = merkle_root_from_txids(txids)

        col1, col2, col3 = st.columns(3)
        col1.metric("Transactions", f"{len(txids):,}")
        col2.metric("Proof steps", len(proof))
        col3.metric("Verified", "Yes" if computed_root == header_root == full_tree_root else "No")

        st.write(f"Block hash: `{block_hash}`")
        st.write(f"Selected txid: `{selected_txid}`")
        st.write(f"Header Merkle root: `{header_root}`")
        st.write(f"Computed proof root: `{computed_root}`")
        st.write(f"Full tree root: `{full_tree_root}`")

        if computed_root == header_root == full_tree_root:
            st.success("Merkle proof verified: the transaction belongs to this block.")
        else:
            st.error("Merkle proof failed.")

        st.subheader("Proof steps")
        st.dataframe(pd.DataFrame(steps), width="stretch")
    except Exception as exc:
        st.error(f"Error verifying Merkle proof: {exc}")
