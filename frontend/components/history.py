"""
Query history component for the Streamlit UI sidebar.
"""

import streamlit as st


def render_history_sidebar(history: list[dict]) -> int | None:
    """
    Render query history in the sidebar.

    Args:
        history: List of query history items.

    Returns:
        Index of clicked history item, or None.
    """
    st.sidebar.markdown("## 📜 Query History")

    if not history:
        st.sidebar.info("No queries yet. Ask a question to get started!")
        return None

    selected_index = None

    for i, item in enumerate(reversed(history)):
        idx = len(history) - 1 - i
        question = item.get("question", "Unknown")
        status = item.get("status", "")
        timestamp = item.get("timestamp", "")

        # Status indicator
        status_emoji = {
            "success": "✅",
            "corrected": "🔄",
            "failed": "❌",
            "error": "⚠️",
            "out_of_scope": "🚫",
        }.get(status, "❓")

        # Truncate question
        display_q = question[:50] + "..." if len(question) > 50 else question

        # Time display
        time_display = ""
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_display = dt.strftime("%H:%M")
            except (ValueError, TypeError):
                pass

        # Clickable history item
        label = f"{status_emoji} {display_q}"
        if time_display:
            label += f" ({time_display})"

        if st.sidebar.button(label, key=f"history_{idx}", use_container_width=True):
            selected_index = idx

    # Clear history button
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear History", use_container_width=True):
        st.session_state["query_history"] = []
        st.session_state["messages"] = []
        st.rerun()

    return selected_index
