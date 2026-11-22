"""
SQL Validator node.

Validates generated SQL for safety before execution.
"""

import logging
from typing import Any

from app.services.sql_safety import validate_sql

logger = logging.getLogger(__name__)


def sql_validator_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Validate generated SQL for safety.

    Updates state with:
    - sql_valid: bool
    - validated_sql: str
    - validation_error: str (if invalid)
    """
    generated_sql = state.get("generated_sql", "")

    logger.info("Validating SQL: %s", generated_sql[:100])

    result = validate_sql(generated_sql)

    if result.is_valid:
        logger.info("SQL validation passed")
        return {
            "sql_valid": True,
            "validated_sql": result.cleaned_sql,
            "validation_error": "",
        }
    else:
        logger.warning("SQL validation failed: %s", result.reason)
        return {
            "sql_valid": False,
            "validated_sql": "",
            "validation_error": result.reason,
            "status": "failed",
            "final_answer": (
                "I generated a query that couldn't pass safety validation: "
                f"{result.reason}. Please try rephrasing your question."
            ),
        }
