"""
API client for communicating with the AgenticSQL backend.

Used by the Streamlit frontend to call the FastAPI backend.
"""

import os
from typing import Any

import httpx


class AgenticSQLClient:
    """HTTP client for the AgenticSQL backend API."""

    def __init__(self, base_url: str | None = None, timeout: float = 120.0):
        self.base_url = base_url or os.environ.get("BACKEND_URL", "http://localhost:8000")
        self.timeout = timeout

    def query(self, question: str, session_id: str = "default") -> dict[str, Any]:
        """
        Send a natural language question to the backend.

        Args:
            question: The user's question.
            session_id: Session identifier for conversation context.

        Returns:
            Response dictionary with answer, SQL, chart, etc.
        """
        response = httpx.post(
            f"{self.base_url}/api/query",
            json={"question": question, "session_id": session_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_schema(self) -> dict[str, Any]:
        """Get database schema information."""
        response = httpx.get(
            f"{self.base_url}/api/schema",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_health(self) -> dict[str, Any]:
        """Check backend health."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/health",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"status": "unreachable", "database": "unknown"}

    def get_history(self, session_id: str = "default") -> dict[str, Any]:
        """Get query history for a session."""
        response = httpx.get(
            f"{self.base_url}/api/query/history",
            params={"session_id": session_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def clear_history(self, session_id: str = "default") -> dict[str, Any]:
        """Clear query history for a session."""
        response = httpx.delete(
            f"{self.base_url}/api/query/history",
            params={"session_id": session_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def upload_dataset(self, session_id: str, file_name: str, file_bytes: bytes) -> dict[str, Any]:
        """
        Upload a CSV dataset to the backend in-memory session database.
        
        Args:
            session_id: The session ID.
            file_name: The name of the file.
            file_bytes: The raw bytes of the CSV file.
            
        Returns:
            Response dictionary with upload status.
        """
        files = {"file": (file_name, file_bytes, "text/csv")}
        data = {"session_id": session_id}
        response = httpx.post(
            f"{self.base_url}/api/session/upload",
            files=files,
            data=data,
            timeout=self.timeout,
        )
        
        if response.status_code != 200:
            try:
                error_detail = response.json().get("detail", "Upload failed")
            except Exception:
                error_detail = response.text
            raise Exception(error_detail)
            
        return response.json()
