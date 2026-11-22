"""
Chat input component for the Streamlit UI.
"""

import streamlit as st


def render_chat_input() -> str | None:
    """
    Render the chat input area and return the submitted question.

    Returns:
        The user's question if submitted, None otherwise.
    """
    st.markdown("### 💬 Ask a question about your data")

    # Example questions
    examples = [
        "What were the top 5 products by revenue?",
        "Show monthly revenue for 2025",
        "Which country has the most customers?",
        "Compare revenue between 2024 and 2025",
        "Who are our top 10 customers by spending?",
        "Which category generated the highest profit?",
    ]

    # Example chips
    cols = st.columns(3)
    for i, example in enumerate(examples):
        col = cols[i % 3]
        if col.button(
            f"💡 {example}",
            key=f"example_{i}",
            use_container_width=True,
        ):
            st.session_state["pending_question"] = example

    st.markdown("---")

    # Main input
    question = st.text_area(
        "Your question:",
        value=st.session_state.get("pending_question", ""),
        height=80,
        placeholder="e.g., What was our total revenue in 2025?",
        key="question_input",
        label_visibility="collapsed",
    )

    # Clear pending question after it's been placed in the text area
    if "pending_question" in st.session_state:
        del st.session_state["pending_question"]

    col1, col2, col3 = st.columns([1, 1, 4])
    submitted = col1.button("🔍 Analyze", type="primary", use_container_width=True)
    if col2.button("🗑️ Clear Chat", use_container_width=True):
        import uuid
        st.session_state["messages"] = []
        st.session_state["query_history"] = []
        st.session_state["current_result"] = None
        st.session_state["session_id"] = str(uuid.uuid4())[:8]
        st.rerun()

    if submitted and question and question.strip():
        return question.strip()

    return None
