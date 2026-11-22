"""
Response Builder node.

Assembles the final response including answer text, SQL explanation,
and chart generation.
"""

import json
import logging
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.sql_explainer import SQL_EXPLAINER_HUMAN, SQL_EXPLAINER_SYSTEM
from app.services.chart_generator import generate_chart
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def response_builder_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Build the final response with answer, explanation, and chart.

    Updates state with:
    - final_answer: str
    - sql_explanation: str
    - chart_json: str (Plotly figure as JSON)
    - status: str
    """
    is_data_question = state.get("is_data_question", True)
    sql_error = state.get("sql_error", "")
    validation_error = state.get("validation_error", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # --- Handle non-data questions ---
    if not is_data_question:
        return {
            "final_answer": (
                "This question is outside the scope of the connected database or uploaded dataset. "
                "I can help you analyze any tables and columns in your data."
            ),
            "status": "out_of_scope",
        }

    # --- Handle failed queries after max retries ---
    if sql_error and retry_count >= max_retries:
        return {
            "final_answer": (
                "I couldn't generate a valid query for this question after "
                f"{max_retries} attempts. Please try rephrasing your question "
                "or providing more specific details."
            ),
            "status": "failed",
        }

    # --- Handle validation failures ---
    if validation_error:
        return {
            "final_answer": state.get("final_answer", "Query validation failed."),
            "status": "failed",
        }

    # --- Build successful response ---
    insights_raw = state.get("insights", "")
    generated_sql = state.get("generated_sql", "")
    df_data = state.get("dataframe", {})
    chart_config = state.get("chart_config", {})

    # Parse insights
    try:
        insights_data = json.loads(insights_raw) if insights_raw else {}
    except json.JSONDecodeError:
        insights_data = {"summary": insights_raw, "insights": []}

    summary = insights_data.get("summary", "")
    insight_bullets = insights_data.get("insights", [])

    # Build answer text
    answer_parts = []
    if summary:
        answer_parts.append(summary)
    if insight_bullets:
        answer_parts.append("")  # blank line
        for bullet in insight_bullets:
            answer_parts.append(f"• {bullet}")

    final_answer = "\n".join(answer_parts) if answer_parts else "Query executed successfully."

    # --- Generate SQL explanation ---
    sql_explanation = ""
    if generated_sql:
        try:
            llm = get_default_llm()
            system_msg = SystemMessage(content=SQL_EXPLAINER_SYSTEM)
            human_msg = HumanMessage(
                content=SQL_EXPLAINER_HUMAN.format(sql_query=generated_sql)
            )
            response = llm.invoke([system_msg, human_msg])
            sql_explanation = response.content.strip()
        except Exception as e:
            logger.warning("SQL explanation failed: %s", e)
            sql_explanation = "Could not generate explanation."

    # --- Generate chart ---
    chart_json = ""
    if df_data and df_data.get("data") and chart_config:
        try:
            df = pd.DataFrame(df_data["data"])
            chart_json = generate_chart(df, chart_config)
        except Exception as e:
            logger.warning("Chart generation failed: %s", e)
            chart_json = ""

    # Determine status
    status = state.get("status", "success")
    if status not in ("corrected", "failed", "out_of_scope"):
        status = "success"

    logger.info("Response built: status=%s, answer_length=%d", status, len(final_answer))

    return {
        "final_answer": final_answer,
        "sql_explanation": sql_explanation,
        "chart_json": chart_json,
        "status": status,
    }
