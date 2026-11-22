"""
Visualizer node.

Determines the appropriate chart type and configuration
based on the query results.
"""

import json
import logging
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.visualizer import VISUALIZER_HUMAN, VISUALIZER_SYSTEM
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def visualizer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Determine the best chart type and configuration for the query results.

    Updates state with:
    - chart_config: dict with chart_type, x_axis, y_axis, title, color_column
    """
    question = state["user_question"]
    df_data = state.get("dataframe", {})

    if not df_data or not df_data.get("data"):
        logger.info("No data for visualization")
        return {
            "chart_config": {"chart_type": "none", "title": "No data to visualize"},
        }

    # Reconstruct DataFrame
    df = pd.DataFrame(df_data["data"])
    columns = df.columns.tolist()
    num_rows = len(df)

    # Determine column types
    column_types = {}
    for col in columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            column_types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            column_types[col] = "datetime"
        else:
            # Check if it looks like a date string
            try:
                pd.to_datetime(df[col].head(3))
                column_types[col] = "datetime"
            except (ValueError, TypeError):
                column_types[col] = "categorical"

    # Sample data for context
    sample_data = df.head(5).to_string(index=False)

    logger.info("Determining visualization for %d rows, %d columns", num_rows, len(columns))

    llm = get_default_llm()
    system_msg = SystemMessage(content=VISUALIZER_SYSTEM)
    human_msg = HumanMessage(
        content=VISUALIZER_HUMAN.format(
            question=question,
            columns=", ".join(columns),
            column_types=json.dumps(column_types),
            num_rows=num_rows,
            sample_data=sample_data,
        )
    )

    try:
        response = llm.invoke([system_msg, human_msg])
        response_text = response.content.strip()

        # Parse JSON response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        chart_config = json.loads(response_text)

        # Validate chart config
        valid_types = {"bar", "horizontal_bar", "line", "pie", "scatter", "histogram", "metric", "table", "none"}
        if chart_config.get("chart_type") not in valid_types:
            chart_config["chart_type"] = "table"

        logger.info("Chart config: %s", chart_config)

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Visualization config parsing failed: %s", e)
        # Fallback: use heuristic chart selection
        chart_config = _heuristic_chart_selection(df, columns, column_types, question)

    return {
        "chart_config": chart_config,
    }


def _heuristic_chart_selection(
    df: pd.DataFrame,
    columns: list[str],
    column_types: dict[str, str],
    question: str,
) -> dict[str, Any]:
    """
    Fallback heuristic chart selection when LLM response fails.
    """
    numeric_cols = [c for c, t in column_types.items() if t == "numeric"]
    categorical_cols = [c for c, t in column_types.items() if t == "categorical"]
    datetime_cols = [c for c, t in column_types.items() if t == "datetime"]

    num_rows = len(df)

    # Single metric
    if num_rows == 1 and len(numeric_cols) <= 2:
        return {
            "chart_type": "metric",
            "x_axis": columns[0],
            "y_axis": numeric_cols[0] if numeric_cols else columns[0],
            "title": "Result",
        }

    # Time series
    if datetime_cols and numeric_cols:
        return {
            "chart_type": "line",
            "x_axis": datetime_cols[0],
            "y_axis": numeric_cols[0],
            "title": "Trend Over Time",
        }

    # Category comparison
    if categorical_cols and numeric_cols:
        if num_rows <= 8:
            return {
                "chart_type": "bar",
                "x_axis": categorical_cols[0],
                "y_axis": numeric_cols[0],
                "title": "Comparison",
            }
        else:
            return {
                "chart_type": "horizontal_bar",
                "x_axis": numeric_cols[0],
                "y_axis": categorical_cols[0],
                "title": "Ranking",
            }

    # Default to table
    return {
        "chart_type": "table",
        "x_axis": columns[0] if columns else "",
        "y_axis": columns[1] if len(columns) > 1 else columns[0] if columns else "",
        "title": "Query Results",
    }
