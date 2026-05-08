"""Bitcoin difficulty history module."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from api.blockchain_client import get_blocks_by_heights, get_tip_height


BLOCKS_PER_ADJUSTMENT = 2016
TARGET_BLOCK_SECONDS = 600


@st.cache_data(ttl=600)
def load_adjustment_periods(period_count: int) -> pd.DataFrame:
    """Load difficulty adjustment boundary blocks and compute period ratios."""
    tip_height = get_tip_height()
    latest_boundary = tip_height - (tip_height % BLOCKS_PER_ADJUSTMENT)
    heights = [
        latest_boundary - index * BLOCKS_PER_ADJUSTMENT
        for index in range(period_count, -1, -1)
    ]
    blocks = get_blocks_by_heights(heights)

    rows = []
    for start, end in zip(blocks, blocks[1:]):
        actual_seconds = end["timestamp"] - start["timestamp"]
        expected_seconds = (end["height"] - start["height"]) * TARGET_BLOCK_SECONDS
        rows.append(
            {
                "Period start": start["height"],
                "Adjustment height": end["height"],
                "Adjustment date": pd.to_datetime(end["timestamp"], unit="s", utc=True),
                "Difficulty": end["difficulty"],
                "Actual days": actual_seconds / 86_400,
                "Expected days": expected_seconds / 86_400,
                "Actual/target ratio": actual_seconds / expected_seconds,
                "Average block minutes": actual_seconds / (end["height"] - start["height"]) / 60,
            }
        )

    return pd.DataFrame(rows)


def render() -> None:
    """Render the M3 panel."""
    st.header("M3 - Difficulty History")
    st.caption("Difficulty evolution across 2016-block adjustment periods.")

    period_count = st.slider("Completed adjustment periods", min_value=3, max_value=12, value=6, key="m3_periods")

    with st.spinner("Loading adjustment periods..."):
        try:
            df = load_adjustment_periods(period_count)
            df["Difficulty change %"] = df["Difficulty"].pct_change() * 100

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["Adjustment date"],
                    y=df["Difficulty"],
                    mode="lines+markers",
                    name="Difficulty adjustment",
                )
            )
            for _, row in df.iterrows():
                fig.add_vline(x=row["Adjustment date"], line_width=1, line_dash="dot", line_color="gray")
            fig.update_layout(
                title="Bitcoin difficulty at each 2016-block adjustment",
                xaxis_title="Adjustment date",
                yaxis_title="Difficulty",
            )
            st.plotly_chart(fig, width="stretch")

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            change = latest["Difficulty change %"] if pd.notna(latest["Difficulty change %"]) else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Latest difficulty", f"{latest['Difficulty']:,.2f}", f"{change:,.2f}%")
            col2.metric("Latest avg block time", f"{latest['Average block minutes']:,.2f} min")
            col3.metric("Actual / target time", f"{latest['Actual/target ratio']:,.3f}")

            ratio_fig = px.bar(
                df,
                x="Adjustment height",
                y="Actual/target ratio",
                title="Actual period duration compared with the 600-second target",
                labels={"Actual/target ratio": "Actual / target", "Adjustment height": "Adjustment height"},
            )
            ratio_fig.add_hline(y=1, line_dash="dash", line_color="red")
            st.plotly_chart(ratio_fig, width="stretch")

            st.write(
                f"The last completed period started at height **{int(previous['Adjustment height'])}** "
                f"and adjusted at **{int(latest['Adjustment height'])}**. "
                f"A ratio below 1 means blocks arrived faster than 10 minutes on average."
            )

            with st.expander("Adjustment period data"):
                st.dataframe(df, width="stretch")
        except Exception as exc:
            st.error(f"Error loading chart: {exc}")
