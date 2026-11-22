"""
Visualization component for the Streamlit UI.
"""

import json

import plotly.io as pio
import streamlit as st


def render_visualization(chart_json: str, title: str = "Visualization") -> None:
    """
    Render a Plotly chart from JSON.

    Args:
        chart_json: Plotly figure serialized as JSON string.
        title: Section title.
    """
    if not chart_json:
        return

    st.markdown(f"### 📊 {title}")

    try:
        fig = pio.from_json(chart_json)

        # Update layout for Streamlit dark theme compatibility
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=440,
        )

        st.plotly_chart(fig, use_container_width=True, key="main_chart")

    except (json.JSONDecodeError, Exception) as e:
        st.warning(f"Could not render chart: {e}")
