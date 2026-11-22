"""
Pydantic request/response schemas for the API.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Request body for the /api/query endpoint."""
    question: str = Field(..., min_length=1, max_length=2000, description="Natural language question")
    session_id: str = Field(default="default", description="Session ID for conversation context")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class QueryResponse(BaseModel):
    """Response from the /api/query endpoint."""
    answer: str = Field(..., description="Natural language answer")
    sql: str = Field(default="", description="Generated SQL query")
    sql_explanation: str = Field(default="", description="Plain-English SQL explanation")
    chart_json: str = Field(default="", description="Plotly chart as JSON")
    insights: str = Field(default="", description="Business insights as JSON")
    execution_time: float = Field(default=0.0, description="SQL execution time in seconds")
    total_time: float = Field(default=0.0, description="Total processing time in seconds")
    retry_count: int = Field(default=0, description="Number of SQL correction attempts")
    status: str = Field(default="success", description="Query status: success/corrected/failed/out_of_scope/error")
    query_result: list[dict[str, Any]] = Field(default_factory=list, description="Raw query results (first N rows)")
    columns: list[str] = Field(default_factory=list, description="Column names")
    total_rows: int = Field(default=0, description="Total result row count")


class QueryHistoryItem(BaseModel):
    """A single item in query history."""
    question: str
    sql: str = ""
    status: str = ""
    execution_time: float = 0.0
    retry_count: int = 0
    timestamp: str = ""
    answer: str = ""


class QueryHistoryResponse(BaseModel):
    """Response for query history endpoint."""
    history: list[QueryHistoryItem] = Field(default_factory=list)
    session_id: str = ""


class SchemaTableInfo(BaseModel):
    """Schema information for a single table."""
    table_name: str
    columns: list[dict[str, Any]]
    primary_keys: list[str]
    foreign_keys: list[dict[str, str]]


class SchemaResponse(BaseModel):
    """Response from the /api/schema endpoint."""
    tables: list[SchemaTableInfo] = Field(default_factory=list)
    relationships: list[dict[str, str]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response from the /api/health endpoint."""
    status: str
    database: str
    message: str = ""
    version: str = "1.0.0"
