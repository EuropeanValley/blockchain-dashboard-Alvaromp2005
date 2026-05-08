"""Optional M7: second AI approach for difficulty prediction."""

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.m3_difficulty_history import load_adjustment_periods


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Fit y = slope*x + intercept without external ML dependencies."""
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0, y_mean
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    return slope, intercept


def walk_forward_predictions(values: list[float]) -> list[dict]:
    """Evaluate simple regression by predicting each later point from previous points."""
    rows = []
    for index in range(3, len(values)):
        xs = list(range(index))
        ys = values[:index]
        slope, intercept = linear_fit(xs, ys)
        prediction = slope * index + intercept
        actual = values[index]
        rows.append(
            {
                "Index": index,
                "Actual": actual,
                "Predicted": prediction,
                "Absolute error": abs(actual - prediction),
                "APE %": abs(actual - prediction) / actual * 100 if actual else 0,
            }
        )
    return rows


def render() -> None:
    """Render the M7 panel."""
    st.header("M7 - Second AI Approach")
    st.caption("Difficulty predictor using walk-forward linear regression on adjustment periods.")

    period_count = st.slider("Adjustment periods for training", 6, 18, 10, key="m7_periods")

    try:
        df = load_adjustment_periods(period_count)
        values = df["Difficulty"].astype(float).tolist()
        evaluation = pd.DataFrame(walk_forward_predictions(values))

        slope, intercept = linear_fit(list(range(len(values))), values)
        next_index = len(values)
        next_prediction = slope * next_index + intercept
        current = values[-1]
        predicted_change = (next_prediction - current) / current * 100

        mae = evaluation["Absolute error"].mean() if not evaluation.empty else 0
        mape = evaluation["APE %"].mean() if not evaluation.empty else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Predicted next difficulty", f"{next_prediction:,.2f}", f"{predicted_change:,.2f}%")
        col2.metric("Walk-forward MAE", f"{mae:,.2f}")
        col3.metric("Walk-forward MAPE", f"{mape:,.2f}%")

        plot_df = df.reset_index(names="Index")
        plot_df["Type"] = "Actual"
        prediction_row = pd.DataFrame(
            [
                {
                    "Index": next_index,
                    "Adjustment date": plot_df["Adjustment date"].iloc[-1] + pd.Timedelta(days=14),
                    "Difficulty": next_prediction,
                    "Type": "Predicted next",
                }
            ]
        )
        chart_df = pd.concat([plot_df[["Index", "Adjustment date", "Difficulty", "Type"]], prediction_row])
        fig = px.line(
            chart_df,
            x="Adjustment date",
            y="Difficulty",
            color="Type",
            markers=True,
            title="Difficulty prediction from recent adjustment periods",
        )
        st.plotly_chart(fig, width="stretch")

        st.write(
            "This second AI approach is intentionally simple and transparent: it learns a linear trend from recent "
            "difficulty adjustments, then evaluates itself with walk-forward predictions."
        )
        with st.expander("Walk-forward evaluation"):
            st.dataframe(evaluation, width="stretch")
    except Exception as exc:
        st.error(f"Error running difficulty predictor: {exc}")
