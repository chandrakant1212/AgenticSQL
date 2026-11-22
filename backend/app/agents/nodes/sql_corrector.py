"""
SQL Corrector node.

Generates corrected SQL based on error analysis.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.sql_corrector import (
    SQL_CORRECTOR_HUMAN,
    SQL_CORRECTOR_SYSTEM,
)
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def sql_corrector_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate corrected SQL based on error analysis.

    Updates state with:
    - generated_sql: str (the corrected SQL, overwrites the failed one)
    - status: str (set to "corrected")
    """
    question = state["user_question"]
    failed_sql = state.get("generated_sql", "")
    error_message = state.get("sql_error", "")
    error_analysis = state.get("error_analysis", "")
    schema_context = state.get("relevant_schema", "")
    retry_count = state.get("retry_count", 0)

    logger.info("Correcting SQL (attempt %d): %s", retry_count, failed_sql[:200])

    llm = get_default_llm()
    system_msg = SystemMessage(
        content=SQL_CORRECTOR_SYSTEM.format(schema_context=schema_context)
    )
    human_msg = HumanMessage(
        content=SQL_CORRECTOR_HUMAN.format(
            question=question,
            failed_sql=failed_sql,
            error_message=error_message,
            error_analysis=error_analysis,
        )
    )

    response = llm.invoke([system_msg, human_msg])
    corrected_sql = response.content.strip()

    # Clean up LLM formatting
    if corrected_sql.startswith("```"):
        lines = corrected_sql.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        corrected_sql = "\n".join(lines).strip()

    if corrected_sql.lower().startswith("sql\n"):
        corrected_sql = corrected_sql[4:].strip()

    logger.info("Corrected SQL: %s", corrected_sql[:200])

    return {
        "generated_sql": corrected_sql,
        "status": "corrected",
    }
