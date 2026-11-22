"""
SQL Generator node.

Generates PostgreSQL SQL from the user's natural-language question
using the relevant schema context.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.sql_generator import SQL_GENERATOR_HUMAN, SQL_GENERATOR_SYSTEM
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def sql_generator_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate SQL from the user's question and schema context.

    Updates state with:
    - generated_sql: str
    """
    question = state["user_question"]
    schema_context = state.get("relevant_schema", "")
    conversation_history = state.get("conversation_history", [])

    logger.info("SQL generator processing: %s", question[:100])

    # Build conversation context for follow-up questions
    conversation_context = ""
    if conversation_history:
        recent = conversation_history[-6:]
        lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        conversation_context = "Recent conversation:\n" + "\n".join(lines)

    # Call LLM
    llm = get_default_llm()
    system_msg = SystemMessage(
        content=SQL_GENERATOR_SYSTEM.format(schema_context=schema_context)
    )
    human_msg = HumanMessage(
        content=SQL_GENERATOR_HUMAN.format(
            question=question,
            conversation_context=conversation_context,
        )
    )

    response = llm.invoke([system_msg, human_msg])
    generated_sql = response.content.strip()

    # Clean up common LLM formatting issues
    if generated_sql.startswith("```"):
        lines = generated_sql.split("\n")
        # Remove first and last lines (code fence markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        generated_sql = "\n".join(lines).strip()

    # Remove any "sql" language tag
    if generated_sql.lower().startswith("sql\n"):
        generated_sql = generated_sql[4:].strip()

    logger.info("Generated SQL: %s", generated_sql[:200])

    return {
        "generated_sql": generated_sql,
    }
