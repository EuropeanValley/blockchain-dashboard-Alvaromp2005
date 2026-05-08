"""Optional M6: Bitcoin security score and 51% attack estimate."""

import pandas as pd
import plotly.express as px
import streamlit as st

from api.blockchain_client import get_latest_blockstream_block, get_recent_blocks
from modules.bitcoin_utils import (
    block_intervals,
    estimate_hashrate,
    format_hashrate,
    format_large_number,
    nakamoto_attack_probability,
)


@st.cache_data(ttl=300)
def load_security_data(block_count: int) -> tuple[dict, float, float]:
    """Load live hash rate inputs."""
    latest = get_latest_blockstream_block()
    intervals = block_intervals(get_recent_blocks(block_count))
    avg_seconds = sum(item["interval_seconds"] for item in intervals) / len(intervals)
    hashrate = estimate_hashrate(latest.get("difficulty"), avg_seconds)
    return latest, avg_seconds, hashrate or 0


def render() -> None:
    """Render the M6 panel."""
    st.header("M6 - Security Score")
    st.caption("Estimate the live cost of matching Bitcoin's hash rate and model confirmation risk.")

    block_count = st.slider("Blocks for hash-rate estimate", 30, 120, 60, step=10, key="m6_blocks")
    attacker_share = st.slider("Attacker hash-rate share", 0.05, 0.49, 0.30, step=0.01, key="m6_share")
    efficiency = st.number_input("ASIC efficiency (J/TH)", min_value=5.0, max_value=60.0, value=15.0, step=1.0)
    electricity_price = st.number_input("Electricity price ($/kWh)", min_value=0.01, max_value=0.50, value=0.06, step=0.01)
    hardware_cost_per_th = st.number_input("Hardware cost ($/TH/s)", min_value=1.0, max_value=50.0, value=12.0, step=1.0)

    try:
        latest, avg_seconds, network_hashrate = load_security_data(block_count)
        attack_hashrate = network_hashrate * attacker_share / (1 - attacker_share)
        attack_th = attack_hashrate / 1e12
        energy_kw = attack_th * efficiency / 1000
        energy_cost_hour = energy_kw * electricity_price
        hardware_cost = attack_th * hardware_cost_per_th

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Network hash rate", format_hashrate(network_hashrate))
        col2.metric("Avg block time", f"{avg_seconds / 60:,.2f} min")
        col3.metric("Attack hash rate", format_hashrate(attack_hashrate))
        col4.metric("Security score", f"{min(100, latest.get('difficulty', 0) / 1e12):,.1f}/100")

        st.subheader("Estimated 51%-style resource cost")
        cost1, cost2 = st.columns(2)
        cost1.metric("Energy cost per hour", f"${energy_cost_hour:,.0f}")
        cost2.metric("Approx. hardware cost", f"${hardware_cost:,.0f}")
        st.write(
            "These are simplified estimates based on live hash rate, selected ASIC efficiency and electricity price. "
            "They do not include logistics, cooling, pool coordination, hardware availability or market impact."
        )

        rows = []
        for confirmations in range(1, 13):
            rows.append(
                {
                    "Confirmations": confirmations,
                    "Attack success probability": nakamoto_attack_probability(attacker_share, confirmations),
                }
            )
        risk_df = pd.DataFrame(rows)
        fig = px.line(
            risk_df,
            x="Confirmations",
            y="Attack success probability",
            markers=True,
            title="Double-spend success probability vs confirmations",
        )
        st.plotly_chart(fig, width="stretch")
        st.dataframe(risk_df, width="stretch")
    except Exception as exc:
        st.error(f"Error estimating security score: {exc}")
