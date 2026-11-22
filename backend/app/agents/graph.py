"""
LangGraph agent workflow definition.

Defines the complete agentic workflow with:
- Query planning and schema retrieval
- SQL generation, validation, and execution
- Self-correction loop with retry limits
- Data analysis, visualization, and response building

Workflow:
    START → query_planner → [is_data_question?]
        No  → response_builder → END
        Yes → sql_generator → sql_validator → [sql_valid?]
            No  → response_builder → END
            Yes → sql_executor → [has_error?]
                No  → data_analyzer → visualizer → response_builder → END
                Yes → [retry_count < max_retries?]
                    Yes → error_analyzer → sql_corrector → sql_validator (loop)
                    No  → response_builder → END
"""

import logging
import time
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.data_analyzer import data_analyzer_node
from app.agents.nodes.error_analyzer import error_analyzer_node
from app.agents.nodes.query_planner import query_planner_node
from app.agents.nodes.response_builder import response_builder_node
from app.agents.nodes.sql_corrector import sql_corrector_node
from app.agents.nodes.sql_executor import sql_executor_node
from app.agents.nodes.sql_generator import sql_generator_node
from app.agents.nodes.sql_validator import sql_validator_node
from app.agents.nodes.visualizer import visualizer_node
from app.agents.state import DEFAULT_STATE, AgentState
from app.config import get_settings
from app.services.conversation import get_conversation_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Router functions (conditional edges)
# ---------------------------------------------------------------------------

def route_after_planner(state: dict[str, Any]) -> Literal["sql_generator", "response_builder"]:
    """Route based on whether the question is answerable from the database."""
    if state.get("is_data_question", True):
        return "sql_generator"
    return "response_builder"


def route_after_validator(state: dict[str, Any]) -> Literal["sql_executor", "response_builder"]:
    """Route based on SQL validation result."""
    if state.get("sql_valid", False):
        return "sql_executor"
    return "response_builder"


def route_after_executor(
    state: dict[str, Any],
) -> Literal["data_analyzer", "error_analyzer", "response_builder"]:
    """Route based on SQL execution result."""
    sql_error = state.get("sql_error", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if not sql_error:
        # Success — proceed to analysis
        return "data_analyzer"
    elif retry_count < max_retries:
        # Error but retries remaining — analyze and correct
        return "error_analyzer"
    else:
        # Error and max retries exceeded — fail gracefully
        return "response_builder"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_agent_graph() -> StateGraph:
    """
    Build and compile the LangGraph agent workflow.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(AgentState)

    # --- Add nodes ---
    graph.add_node("query_planner", query_planner_node)
    graph.add_node("sql_generator", sql_generator_node)
    graph.add_node("sql_validator", sql_validator_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("error_analyzer", error_analyzer_node)
    graph.add_node("sql_corrector", sql_corrector_node)
    graph.add_node("data_analyzer", data_analyzer_node)
    graph.add_node("visualizer", visualizer_node)
    graph.add_node("response_builder", response_builder_node)

    # --- Add edges ---

    # START → query_planner
    graph.add_edge(START, "query_planner")

    # query_planner → [conditional] → sql_generator OR response_builder
    graph.add_conditional_edges(
        "query_planner",
        route_after_planner,
        {
            "sql_generator": "sql_generator",
            "response_builder": "response_builder",
        },
    )

    # sql_generator → sql_validator
    graph.add_edge("sql_generator", "sql_validator")

    # sql_validator → [conditional] → sql_executor OR response_builder
    graph.add_conditional_edges(
        "sql_validator",
        route_after_validator,
        {
            "sql_executor": "sql_executor",
            "response_builder": "response_builder",
        },
    )

    # sql_executor → [conditional] → data_analyzer OR error_analyzer OR response_builder
    graph.add_conditional_edges(
        "sql_executor",
        route_after_executor,
        {
            "data_analyzer": "data_analyzer",
            "error_analyzer": "error_analyzer",
            "response_builder": "response_builder",
        },
    )

    # error_analyzer → sql_corrector
    graph.add_edge("error_analyzer", "sql_corrector")

    # sql_corrector → sql_validator (re-enters validation loop)
    graph.add_edge("sql_corrector", "sql_validator")

    # data_analyzer → visualizer
    graph.add_edge("data_analyzer", "visualizer")

    # visualizer → response_builder
    graph.add_edge("visualizer", "response_builder")

    # response_builder → END
    graph.add_edge("response_builder", END)

    logger.info("Agent graph built successfully")
    return graph.compile()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Cached compiled graph
_compiled_graph = None


def get_agent_graph():
    """Get or create the compiled agent graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph


async def run_agent(
    question: str,
    session_id: str = "default",
) -> dict[str, Any]:
    """
    Run the agent workflow for a user question.

    Args:
        question: The user's natural language question.
        session_id: Session identifier for conversation context.

    Returns:
        The final agent state containing all results.
    """
    settings = get_settings()
    conversation_mgr = get_conversation_manager()

    # Build initial state
    initial_state = {
        **DEFAULT_STATE,
        "session_id": session_id,
        "user_question": question,
        "conversation_history": conversation_mgr.get_context_messages(session_id),
        "max_retries": settings.MAX_RETRY_COUNT,
    }

    logger.info("Running agent for question: %s (session: %s)", question[:100], session_id)
    start_time = time.time()

    try:
        graph = get_agent_graph()
        final_state = graph.invoke(initial_state)

        total_time = time.time() - start_time

        # Update conversation history
        conversation_mgr.add_message(session_id, "user", question)
        conversation_mgr.add_message(
            session_id,
            "assistant",
            final_state.get("final_answer", ""),
            metadata={
                "sql": final_state.get("generated_sql", ""),
                "status": final_state.get("status", ""),
                "execution_time": final_state.get("execution_time", 0),
                "retry_count": final_state.get("retry_count", 0),
            },
        )

        # Add total processing time
        final_state["total_time"] = total_time

        logger.info(
            "Agent completed: status=%s, retries=%d, time=%.2fs",
            final_state.get("status", "unknown"),
            final_state.get("retry_count", 0),
            total_time,
        )

        return final_state

    except Exception as e:
        total_time = time.time() - start_time
        logger.error("Agent execution failed: %s", e, exc_info=True)
        return {
            **DEFAULT_STATE,
            "user_question": question,
            "final_answer": (
                f"An error occurred while processing your question: {str(e)}"
            ),
            "status": "error",
            "sql_error": str(e),
            "total_time": total_time,
        }
