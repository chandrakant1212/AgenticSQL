"""
LangGraph agent state definition.

Defines the shared state that flows through all nodes in the agent graph.
"""

from typing import Annotated, Any, TypedDict
from operator import add


def merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dicts, with right taking precedence."""
    merged = left.copy()
    merged.update(right)
    return merged


class AgentState(TypedDict, total=False):
    """
    State dictionary for the LangGraph agent workflow.
    """
    session_id: str
    user_question: str
    conversation_history: list
    is_data_question: bool
    relevant_tables: list
    relevant_schema: str
    generated_sql: str
    validated_sql: str
    sql_valid: bool
    validation_error: str
    sql_error: str
    error_analysis: str
    retry_count: int
    max_retries: int
    query_result: list
    dataframe: dict
    columns: list
    total_rows: int
    execution_time: float
    chart_config: dict
    chart_json: str
    insights: str
    sql_explanation: str
    final_answer: str
    status: str
    total_time: float


# Default state values for initialization
DEFAULT_STATE = {
    "user_question": "",
    "conversation_history": [],
    "is_data_question": True,
    "relevant_tables": [],
    "relevant_schema": "",
    "generated_sql": "",
    "validated_sql": "",
    "sql_valid": False,
    "validation_error": "",
    "sql_error": "",
    "error_analysis": "",
    "retry_count": 0,
    "max_retries": 3,
    "query_result": [],
    "dataframe": {},
    "columns": [],
    "total_rows": 0,
    "execution_time": 0.0,
    "chart_config": {},
    "chart_json": "",
    "insights": "",
    "sql_explanation": "",
    "final_answer": "",
    "status": "pending",
}
