"""
Query API endpoint.

POST /api/query — Main endpoint for natural language data analysis.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.graph import run_agent
from app.api.schemas import QueryHistoryItem, QueryHistoryResponse, QueryRequest, QueryResponse
from app.services.conversation import get_conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

# In-memory query history per session
_query_history: dict[str, list[dict[str, Any]]] = {}


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    Process a natural language question and return analysis results.

    The endpoint runs the full agentic workflow:
    1. Query understanding and table selection
    2. SQL generation and validation
    3. SQL execution with self-correction
    4. Data analysis and visualization
    5. Response assembly
    """
    logger.info(
        "Query request: question='%s', session='%s'",
        request.question[:100], request.session_id,
    )

    try:
        # Run the agent workflow
        result = await run_agent(
            question=request.question,
            session_id=request.session_id,
        )

        # Build response
        response = QueryResponse(
            answer=result.get("final_answer", ""),
            sql=result.get("generated_sql", ""),
            sql_explanation=result.get("sql_explanation", ""),
            chart_json=result.get("chart_json", ""),
            insights=result.get("insights", ""),
            execution_time=result.get("execution_time", 0.0),
            total_time=result.get("total_time", 0.0),
            retry_count=result.get("retry_count", 0),
            status=result.get("status", "success"),
            query_result=result.get("query_result", [])[:50],  # Limit result preview
            columns=result.get("columns", []),
            total_rows=result.get("total_rows", 0),
        )

        # Save to query history
        _save_to_history(request.session_id, request.question, response)

        return response

    except Exception as e:
        logger.error("Query execution failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your question: {str(e)}",
        )


@router.get("/query/history", response_model=QueryHistoryResponse)
async def get_query_history(session_id: str = "default") -> QueryHistoryResponse:
    """Get query history for a session."""
    history = _query_history.get(session_id, [])
    items = [QueryHistoryItem(**h) for h in history]
    return QueryHistoryResponse(history=items, session_id=session_id)


@router.delete("/query/history")
async def clear_query_history(session_id: str = "default") -> dict:
    """Clear query history for a session."""
    _query_history.pop(session_id, None)
    conversation_mgr = get_conversation_manager()
    conversation_mgr.clear(session_id)
    return {"message": "History cleared", "session_id": session_id}


def _save_to_history(
    session_id: str,
    question: str,
    response: QueryResponse,
) -> None:
    """Save a query to the session history."""
    if session_id not in _query_history:
        _query_history[session_id] = []

    from datetime import datetime

    _query_history[session_id].append({
        "question": question,
        "sql": response.sql,
        "status": response.status,
        "execution_time": response.execution_time,
        "retry_count": response.retry_count,
        "timestamp": datetime.now().isoformat(),
        "answer": response.answer[:200],  # Truncate for history
    })

    # Keep last 50 queries per session
    if len(_query_history[session_id]) > 50:
        _query_history[session_id] = _query_history[session_id][-50:]
