"""
SQL Error Analyzer node.

Analyzes SQL execution errors using the LLM to identify root causes
and suggest fixes.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.error_analyzer import (
    ERROR_ANALYZER_HUMAN,
    ERROR_ANALYZER_SYSTEM,
)
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def error_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze a SQL execution error.

    Updates state with:
    - error_analysis: str (structured analysis of the error)
    """
    failed_sql = state.get("generated_sql", "")
    error_message = state.get("sql_error", "")
    schema_context = state.get("relevant_schema", "")

    logger.info("Analyzing SQL error: %s", error_message[:200])

    llm = get_default_llm()
    system_msg = SystemMessage(
        content=ERROR_ANALYZER_SYSTEM.format(schema_context=schema_context)
    )
    human_msg = HumanMessage(
        content=ERROR_ANALYZER_HUMAN.format(
            failed_sql=failed_sql,
            error_message=error_message,
        )
    )

    try:
        response = llm.invoke([system_msg, human_msg])
        response_text = response.content.strip()

        # Try to parse as JSON
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        analysis = json.loads(response_text)
        error_analysis = json.dumps(analysis)

        logger.info(
            "Error analysis: type=%s, cause=%s",
            analysis.get("error_type", "unknown"),
            analysis.get("root_cause", "unknown")[:100],
        )

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Error analysis parsing failed: %s", e)
        error_analysis = json.dumps({
            "error_type": "unknown",
            "root_cause": error_message,
            "fix_suggestion": "Review the SQL query and schema",
        })

    return {
        "error_analysis": error_analysis,
    }
