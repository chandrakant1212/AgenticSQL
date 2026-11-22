"""
Data Analyzer node.

Analyzes query results and generates business insights using the LLM.
"""

import json
import logging
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.data_analyzer import (
    DATA_ANALYZER_HUMAN,
    DATA_ANALYZER_SYSTEM,
)
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def data_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze query results and generate business insights.

    Updates state with:
    - insights: str (JSON string with summary and insight bullets)
    """
    question = state["user_question"]
    sql_query = state.get("generated_sql", "")
    df_data = state.get("dataframe", {})

    if not df_data or not df_data.get("data"):
        logger.info("No data to analyze")
        return {
            "insights": json.dumps({
                "summary": "The query returned no results.",
                "insights": ["No data found matching your criteria."],
            }),
        }

    # Reconstruct DataFrame
    df = pd.DataFrame(df_data["data"])
    columns = df_data.get("columns", df.columns.tolist())
    total_rows = df_data.get("shape", [len(df)])[0]

    # Prepare results text (limit to first 20 rows for LLM context)
    display_rows = min(20, len(df))
    results_text = df.head(display_rows).to_string(index=False)

    logger.info("Analyzing %d rows of data", total_rows)

    llm = get_default_llm()
    system_msg = SystemMessage(content=DATA_ANALYZER_SYSTEM)
    human_msg = HumanMessage(
        content=DATA_ANALYZER_HUMAN.format(
            question=question,
            sql_query=sql_query,
            num_rows=display_rows,
            results_text=results_text,
            columns=", ".join(columns),
            total_rows=total_rows,
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

        insights_data = json.loads(response_text)
        insights = json.dumps(insights_data)

        logger.info("Data analysis complete: %s", insights_data.get("summary", "")[:100])

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Data analysis parsing failed: %s", e)
        # Fallback: generate basic insights from data
        insights = json.dumps({
            "summary": f"Query returned {total_rows} rows across {len(columns)} columns.",
            "insights": [
                f"The result contains {total_rows} records.",
                f"Columns: {', '.join(columns)}.",
            ],
        })

    return {
        "insights": insights,
    }
