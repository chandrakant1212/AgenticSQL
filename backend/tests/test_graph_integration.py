"""
Integration tests for the LangGraph agent workflow.

These tests verify the complete workflow including routing, retries,
and state management. They require a running database and LLM API.
"""

import pytest

from app.agents.graph import (
    route_after_executor,
    route_after_planner,
    route_after_validator,
)
from app.agents.state import DEFAULT_STATE


class TestRouting:
    """Test conditional routing functions."""

    def test_route_data_question(self):
        """Data questions should route to SQL generator."""
        state = {**DEFAULT_STATE, "is_data_question": True}
        assert route_after_planner(state) == "sql_generator"

    def test_route_non_data_question(self):
        """Non-data questions should route to response builder."""
        state = {**DEFAULT_STATE, "is_data_question": False}
        assert route_after_planner(state) == "response_builder"

    def test_route_valid_sql(self):
        """Valid SQL should route to executor."""
        state = {**DEFAULT_STATE, "sql_valid": True}
        assert route_after_validator(state) == "sql_executor"

    def test_route_invalid_sql(self):
        """Invalid SQL should route to response builder."""
        state = {**DEFAULT_STATE, "sql_valid": False}
        assert route_after_validator(state) == "response_builder"

    def test_route_execution_success(self):
        """Successful execution should route to data analyzer."""
        state = {**DEFAULT_STATE, "sql_error": "", "retry_count": 0}
        assert route_after_executor(state) == "data_analyzer"

    def test_route_execution_error_with_retries(self):
        """Execution error with retries available should route to error analyzer."""
        state = {**DEFAULT_STATE, "sql_error": "column not found", "retry_count": 1, "max_retries": 3}
        assert route_after_executor(state) == "error_analyzer"

    def test_route_execution_error_max_retries(self):
        """Execution error at max retries should route to response builder."""
        state = {**DEFAULT_STATE, "sql_error": "column not found", "retry_count": 3, "max_retries": 3}
        assert route_after_executor(state) == "response_builder"

    def test_route_execution_error_exactly_at_limit(self):
        """Test edge case: retry_count equals max_retries."""
        state = {**DEFAULT_STATE, "sql_error": "error", "retry_count": 3, "max_retries": 3}
        assert route_after_executor(state) == "response_builder"

    def test_route_execution_error_one_below_limit(self):
        """Test edge case: retry_count is one below max_retries."""
        state = {**DEFAULT_STATE, "sql_error": "error", "retry_count": 2, "max_retries": 3}
        assert route_after_executor(state) == "error_analyzer"


class TestStateDefaults:
    """Test default state initialization."""

    def test_default_state_has_all_keys(self):
        """Default state should have all required keys."""
        required_keys = [
            "user_question", "conversation_history", "is_data_question",
            "relevant_tables", "relevant_schema", "generated_sql",
            "validated_sql", "sql_valid", "validation_error",
            "sql_error", "error_analysis", "retry_count", "max_retries",
            "query_result", "dataframe", "columns", "total_rows",
            "execution_time", "chart_config", "chart_json",
            "insights", "sql_explanation", "final_answer", "status",
        ]
        for key in required_keys:
            assert key in DEFAULT_STATE, f"Missing key: {key}"

    def test_default_retry_count_is_zero(self):
        """Retry count should start at zero."""
        assert DEFAULT_STATE["retry_count"] == 0

    def test_default_max_retries(self):
        """Max retries should be 3."""
        assert DEFAULT_STATE["max_retries"] == 3

    def test_default_status(self):
        """Default status should be pending."""
        assert DEFAULT_STATE["status"] == "pending"
