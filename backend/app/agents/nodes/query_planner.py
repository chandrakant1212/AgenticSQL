"""
Query Planner node.

Determines whether the user's question is answerable from the database
and identifies the relevant tables.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.query_planner import QUERY_PLANNER_HUMAN, QUERY_PLANNER_SYSTEM
from app.database.schema_inspector import SchemaInspector
from app.services.llm import get_default_llm

logger = logging.getLogger(__name__)


def query_planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze the user's question and determine relevant tables.

    Updates state with:
    - is_data_question: bool
    - relevant_tables: list[str]
    - relevant_schema: str (schema text for selected tables)
    """
    question = state["user_question"]
    conversation_history = state.get("conversation_history", [])

    logger.info("Query planner processing: %s", question[:100])

    # Get table descriptions for LLM context
    session_id = state.get("session_id", "default")
    from app.database.session_db import get_session_db_manager
    db_mgr = get_session_db_manager()
    session_engine = db_mgr.get_engine(session_id)
    
    inspector = SchemaInspector(engine=session_engine)
    table_descriptions = inspector.get_table_descriptions()
    table_desc_text = "\n".join(
        f"- {name}: {desc}" for name, desc in table_descriptions.items()
    )

    # Build conversation context
    conversation_context = ""
    if conversation_history:
        recent = conversation_history[-6:]  # Last 3 exchanges
        lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        conversation_context = "Recent conversation:\n" + "\n".join(lines)

    # Call LLM
    llm = get_default_llm()
    system_msg = SystemMessage(
        content=QUERY_PLANNER_SYSTEM.format(table_descriptions=table_desc_text)
    )
    human_msg = HumanMessage(
        content=QUERY_PLANNER_HUMAN.format(
            question=question,
            conversation_context=conversation_context,
        )
    )

    try:
        response = llm.invoke([system_msg, human_msg])
        response_text = response.content.strip()

        # Parse JSON response
        # Handle potential markdown code fences
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        is_data_question = result.get("is_data_question", True)
        relevant_tables = result.get("relevant_tables", [])
        reasoning = result.get("reasoning", "")

        logger.info(
            "Query planner result: is_data=%s, tables=%s, reason=%s",
            is_data_question, relevant_tables, reasoning,
        )

        # Get schema text for relevant tables
        relevant_schema = ""
        if is_data_question and relevant_tables:
            # Validate table names against actual database
            all_tables = inspector.get_all_tables()
            valid_tables = [t for t in relevant_tables if t in all_tables]
            if not valid_tables:
                valid_tables = all_tables  # Fallback to all tables
            relevant_schema = inspector.get_tables_schema_text(valid_tables)
            relevant_tables = valid_tables

        return {
            "is_data_question": is_data_question,
            "relevant_tables": relevant_tables,
            "relevant_schema": relevant_schema,
        }

    except (json.JSONDecodeError, Exception) as e:
        logger.error("Query planner failed: %s", e)
        # Fallback: assume it's a data question and include all tables
        all_tables = inspector.get_all_tables()
        return {
            "is_data_question": True,
            "relevant_tables": all_tables,
            "relevant_schema": inspector.get_tables_schema_text(all_tables),
        }
