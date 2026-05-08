"""AI component: statistical anomaly detector for Bitcoin block intervals."""

import pandas as pd
import plotly.express as px
import streamlit as st

from api.blockchain_client import get_recent_blocks
from modules.bitcoin_utils import (
    anomaly_label,
    block_intervals,
    exponential_log_likelihood,
    exponential_tail_probability,
)


@st.cache_data(ttl=300)
def load_anomaly_data(block_count: int) -> pd.DataFrame:
    """Load recent block intervals for anomaly detection."""
    blocks = get_recent_blocks(block_count)
    return pd.DataFrame(block_intervals(blocks))


def render() -> None:
    """Render the M4 panel."""
    st.header("M4 - AI Component")
    st.caption("Anomaly detector trained on recent Bitcoin inter-arrival times.")

    block_count = st.slider("Recent blocks used as training data", 40, 200, 100, step=20, key="m4_blocks")
    tail_threshold = st.slider("Tail probability threshold", 0.01, 0.10, 0.05, step=0.01, key="m4_tail")

    with st.spinner("Training anomaly detector on live block intervals..."):
        try:
            df = load_anomaly_data(block_count)
            mean_seconds = df["interval_seconds"].mean()
            df["model"] = "Exponential baseline"
            df["tail_probability_slow"] = df["interval_seconds"].apply(
                lambda seconds: exponential_tail_probability(seconds, mean_seconds)
            )
            df["label"] = df["interval_seconds"].apply(
                lambda seconds: anomaly_label(seconds, mean_seconds, tail_threshold, 1 - tail_threshold)
            )
            df["is_anomaly"] = df["label"] != "Normal"

            log_likelihood = exponential_log_likelihood(df["interval_seconds"].tolist(), mean_seconds)
            mae_vs_target = (df["interval_seconds"] - 600).abs().mean()
            anomaly_rate = df["is_anomaly"].mean() * 100

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Training intervals", len(df))
            col2.metric("Fitted mean", f"{mean_seconds / 60:,.2f} min")
            col3.metric("MAE vs 600s", f"{mae_vs_target:,.1f} s")
            col4.metric("Anomaly rate", f"{anomaly_rate:,.1f}%")

            st.write(
                "Model choice: an exponential distribution is used because Bitcoin mining is modeled as a "
                "memoryless Poisson process. The detector flags intervals in the extreme tails of the fitted distribution."
            )
            st.write(f"Evaluation metric: total log-likelihood on the recent sample = **{log_likelihood:,.2f}**.")

            fig = px.scatter(
                df,
                x="height",
                y="interval_minutes",
                color="label",
                hover_data=["hash", "tail_probability_slow"],
                title="Detected anomalies in recent Bitcoin block intervals",
                labels={"height": "Block height", "interval_minutes": "Minutes since previous block"},
            )
            fig.add_hline(y=10, line_dash="dash", line_color="green")
            st.plotly_chart(fig, width="stretch")

            anomalies = df[df["is_anomaly"]].sort_values("interval_seconds", ascending=False)
            st.subheader("Flagged blocks")
            if anomalies.empty:
                st.success("No anomalies found with the selected threshold.")
            else:
                st.dataframe(
                    anomalies[
                        [
                            "height",
                            "interval_minutes",
                            "label",
                            "tail_probability_slow",
                            "hash",
                        ]
                    ],
                    width="stretch",
                )

            with st.expander("Training data"):
                st.dataframe(df, width="stretch")
        except Exception as exc:
            st.error(f"Error running anomaly detector: {exc}")
