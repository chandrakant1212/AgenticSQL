"""
Conversation memory management.

Maintains session-based conversation history for follow-up question support.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history for a session.

    Stores the last N messages to provide context for follow-up questions.
    Each message includes role (user/assistant), content, and timestamp.
    """

    def __init__(self, max_messages: int = 20):
        """
        Initialize the conversation manager.

        Args:
            max_messages: Maximum number of messages to retain.
        """
        self._max_messages = max_messages
        self._sessions: dict[str, list[dict[str, Any]]] = {}

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            session_id: The session identifier.
            role: Message role ("user" or "assistant").
            content: Message content.
            metadata: Optional metadata (SQL, status, etc.).
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self._sessions[session_id].append(message)

        # Trim to max_messages
        if len(self._sessions[session_id]) > self._max_messages:
            self._sessions[session_id] = self._sessions[session_id][-self._max_messages:]

        logger.debug(
            "Added %s message to session %s (total: %d)",
            role, session_id, len(self._sessions[session_id]),
        )

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        return self._sessions.get(session_id, [])

    def get_context_messages(self, session_id: str, limit: int = 10) -> list[dict[str, str]]:
        """
        Get recent messages formatted for LLM context.

        Returns simplified messages with just role and content.
        """
        history = self.get_history(session_id)
        recent = history[-limit:] if len(history) > limit else history
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    def clear(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self._sessions.pop(session_id, None)
        logger.info("Cleared conversation for session %s", session_id)

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)


# Singleton instance
_conversation_manager: ConversationManager | None = None


def get_conversation_manager() -> ConversationManager:
    """Get the singleton ConversationManager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
