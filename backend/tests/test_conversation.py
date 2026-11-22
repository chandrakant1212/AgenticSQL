"""
Unit tests for conversation memory management.
"""

import pytest

from app.services.conversation import ConversationManager


class TestConversationManager:
    """Tests for the ConversationManager class."""

    def setup_method(self):
        """Set up a fresh ConversationManager for each test."""
        self.manager = ConversationManager(max_messages=10)

    def test_add_and_get_message(self):
        """Test adding and retrieving messages."""
        self.manager.add_message("session1", "user", "Hello")
        history = self.manager.get_history("session1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_conversation_order(self):
        """Test that messages maintain chronological order."""
        self.manager.add_message("session1", "user", "First")
        self.manager.add_message("session1", "assistant", "Second")
        self.manager.add_message("session1", "user", "Third")

        history = self.manager.get_history("session1")
        assert len(history) == 3
        assert history[0]["content"] == "First"
        assert history[1]["content"] == "Second"
        assert history[2]["content"] == "Third"

    def test_max_messages_limit(self):
        """Test that old messages are trimmed when exceeding max."""
        for i in range(15):
            self.manager.add_message("session1", "user", f"Message {i}")

        history = self.manager.get_history("session1")
        assert len(history) == 10  # max_messages
        assert history[0]["content"] == "Message 5"  # Oldest remaining

    def test_session_isolation(self):
        """Test that sessions are isolated from each other."""
        self.manager.add_message("session1", "user", "Session 1")
        self.manager.add_message("session2", "user", "Session 2")

        h1 = self.manager.get_history("session1")
        h2 = self.manager.get_history("session2")
        assert len(h1) == 1
        assert len(h2) == 1
        assert h1[0]["content"] == "Session 1"
        assert h2[0]["content"] == "Session 2"

    def test_clear_session(self):
        """Test clearing a specific session."""
        self.manager.add_message("session1", "user", "Hello")
        self.manager.add_message("session2", "user", "World")

        self.manager.clear("session1")

        assert len(self.manager.get_history("session1")) == 0
        assert len(self.manager.get_history("session2")) == 1

    def test_get_context_messages(self):
        """Test getting simplified context messages."""
        self.manager.add_message("session1", "user", "Q1", metadata={"sql": "SELECT 1"})
        self.manager.add_message("session1", "assistant", "A1")

        context = self.manager.get_context_messages("session1")
        assert len(context) == 2
        assert "metadata" not in context[0]  # Simplified format
        assert context[0] == {"role": "user", "content": "Q1"}

    def test_context_limit(self):
        """Test that context messages respect the limit."""
        for i in range(20):
            self.manager.add_message("session1", "user", f"Msg {i}")

        context = self.manager.get_context_messages("session1", limit=5)
        assert len(context) == 5

    def test_empty_session(self):
        """Test getting history for a non-existent session."""
        history = self.manager.get_history("nonexistent")
        assert history == []

    def test_metadata_storage(self):
        """Test that metadata is stored with messages."""
        self.manager.add_message("s1", "user", "Q", metadata={"sql": "SELECT 1"})
        history = self.manager.get_history("s1")
        assert history[0]["metadata"]["sql"] == "SELECT 1"

    def test_session_count(self):
        """Test counting active sessions."""
        self.manager.add_message("s1", "user", "a")
        self.manager.add_message("s2", "user", "b")
        assert self.manager.get_session_count() == 2

    def test_timestamps_present(self):
        """Test that timestamps are added to messages."""
        self.manager.add_message("s1", "user", "Hello")
        history = self.manager.get_history("s1")
        assert "timestamp" in history[0]
        assert history[0]["timestamp"]  # Not empty
