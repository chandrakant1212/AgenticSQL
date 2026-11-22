"""
Plotly chart generator.

Generates Plotly charts from structured configuration and DataFrame data.
Uses deterministic chart generation — no arbitrary code execution.
"""

import json
import logging
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# Professional color palette
COLORS = [
    "#6366F1",  # Indigo
    "#8B5CF6",  # Violet
    "#EC4899",  # Pink
    "#F43F5E",  # Rose
    "#F97316",  # Orange
    "#EAB308",  # Yellow
    "#22C55E",  # Green
    "#06B6D4",  # Cyan
    "#3B82F6",  # Blue
    "#A855F7",  # Purple
]

CHART_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#E2E8F0"},
        "xaxis": {
            "gridcolor": "rgba(148,163,184,0.1)",
            "zerolinecolor": "rgba(148,163,184,0.2)",
        },
        "yaxis": {
            "gridcolor": "rgba(148,163,184,0.1)",
            "zerolinecolor": "rgba(148,163,184,0.2)",
        },
        "margin": {"l": 60, "r": 30, "t": 50, "b": 60},
    }
}


def generate_chart(df: pd.DataFrame, config: dict[str, Any]) -> str:
    """
    Generate a Plotly chart from DataFrame and configuration.

    Args:
        df: The data to visualize.
        config: Chart configuration with:
            - chart_type: str
            - x_axis: str (column name)
            - y_axis: str (column name)
            - title: str
            - color_column: str | None

    Returns:
        Plotly figure serialized as JSON string.
    """
    chart_type = config.get("chart_type", "table")
    x_axis = config.get("x_axis", "")
    y_axis = config.get("y_axis", "")
    title = config.get("title", "Chart")
    color_col = config.get("color_column")

    # Validate columns exist
    if x_axis and x_axis not in df.columns:
        logger.warning("x_axis '%s' not in columns: %s", x_axis, df.columns.tolist())
        x_axis = df.columns[0] if len(df.columns) > 0 else ""
    if y_axis and y_axis not in df.columns:
        logger.warning("y_axis '%s' not in columns: %s", y_axis, df.columns.tolist())
        y_axis = df.columns[1] if len(df.columns) > 1 else df.columns[0] if len(df.columns) > 0 else ""
    if color_col and color_col not in df.columns:
        color_col = None

    try:
        fig = _create_chart(df, chart_type, x_axis, y_axis, title, color_col)
        _apply_styling(fig, title)
        return fig.to_json()
    except Exception as e:
        logger.error("Chart generation failed: %s", e)
        # Fallback: create a simple table view
        fig = go.Figure(data=[go.Table(
            header=dict(values=df.columns.tolist()),
            cells=dict(values=[df[col].tolist() for col in df.columns]),
        )])
        _apply_styling(fig, title)
        return fig.to_json()


def _create_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_axis: str,
    y_axis: str,
    title: str,
    color_col: str | None,
) -> go.Figure:
    """Create the appropriate chart type."""

    if chart_type == "bar":
        fig = px.bar(
            df, x=x_axis, y=y_axis,
            color=color_col,
            color_discrete_sequence=COLORS,
        )

    elif chart_type == "horizontal_bar":
        fig = px.bar(
            df, x=y_axis, y=x_axis,
            orientation="h",
            color=color_col,
            color_discrete_sequence=COLORS,
        )

    elif chart_type == "line":
        fig = px.line(
            df, x=x_axis, y=y_axis,
            color=color_col,
            color_discrete_sequence=COLORS,
            markers=True,
        )

    elif chart_type == "pie":
        fig = px.pie(
            df, names=x_axis, values=y_axis,
            color_discrete_sequence=COLORS,
        )

    elif chart_type == "scatter":
        fig = px.scatter(
            df, x=x_axis, y=y_axis,
            color=color_col,
            color_discrete_sequence=COLORS,
        )

    elif chart_type == "histogram":
        fig = px.histogram(
            df, x=x_axis,
            color=color_col,
            color_discrete_sequence=COLORS,
        )

    elif chart_type == "metric":
        # Single value display as indicator
        value = df[y_axis].iloc[0] if y_axis and len(df) > 0 else 0
        label = df[x_axis].iloc[0] if x_axis and x_axis != y_axis and len(df) > 0 else title

        fig = go.Figure(go.Indicator(
            mode="number",
            value=float(value) if isinstance(value, (int, float)) else 0,
            title={"text": str(label)},
            number={"font": {"size": 48, "color": COLORS[0]}},
        ))

    elif chart_type == "table":
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=df.columns.tolist(),
                fill_color="#334155",
                font=dict(color="#E2E8F0", size=13),
                align="left",
            ),
            cells=dict(
                values=[df[col].tolist() for col in df.columns],
                fill_color="#1E293B",
                font=dict(color="#CBD5E1", size=12),
                align="left",
            ),
        )])

    else:
        # Default to table
        fig = go.Figure(data=[go.Table(
            header=dict(values=df.columns.tolist()),
            cells=dict(values=[df[col].tolist() for col in df.columns]),
        )])

    return fig


def _apply_styling(fig: go.Figure, title: str) -> None:
    """Apply consistent styling to the chart."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color="#F1F5F9"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#E2E8F0"),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.1)",
            zerolinecolor="rgba(148,163,184,0.2)",
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.1)",
            zerolinecolor="rgba(148,163,184,0.2)",
        ),
        margin=dict(l=60, r=30, t=50, b=60),
        showlegend=True if fig.data and len(fig.data) > 1 else False,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1"),
        ),
        height=420,
    )
