"""
Query details component for the Streamlit UI.

Shows SQL, explanation, and execution metadata.
"""

import json

import streamlit as st


def render_query_details(result: dict) -> None:
    """
    Render query details including SQL, explanation, and metadata.

    Args:
        result: The query response dictionary.
    """
    sql = result.get("sql", "")
    explanation = result.get("sql_explanation", "")
    execution_time = result.get("execution_time", 0)
    total_time = result.get("total_time", 0)
    retry_count = result.get("retry_count", 0)
    status = result.get("status", "success")

    # --- Status and metrics ---
    st.markdown("### 📋 Query Details")

    col1, col2, col3, col4 = st.columns(4)

    # Status indicator
    status_icons = {
        "success": "✅",
        "corrected": "🔄",
        "failed": "❌",
        "error": "⚠️",
        "out_of_scope": "🚫",
    }
    status_labels = {
        "success": "Success",
        "corrected": "Auto-Corrected",
        "failed": "Failed",
        "error": "Error",
        "out_of_scope": "Out of Scope",
    }

    col1.metric("Status", f"{status_icons.get(status, '❓')} {status_labels.get(status, status)}")
    col2.metric("SQL Execution", f"{execution_time:.2f}s")
    col3.metric("Total Time", f"{total_time:.2f}s")
    col4.metric("Attempts", retry_count + 1 if status != "out_of_scope" else "—")

    if status == "corrected":
        st.info(f"🔄 Query was automatically corrected after {retry_count} attempt(s).")

    # --- SQL ---
    if sql:
        with st.expander("🔍 View SQL", expanded=False):
            st.code(sql, language="sql")

    # --- Explanation ---
    if explanation:
        with st.expander("📖 Query Explanation", expanded=False):
            st.markdown(explanation)

    # --- Raw data preview ---
    query_result = result.get("query_result", [])
    if query_result:
        with st.expander(f"📄 Data Preview ({result.get('total_rows', len(query_result))} rows)", expanded=False):
            import pandas as pd
            df = pd.DataFrame(query_result)
            st.dataframe(df, use_container_width=True, height=300)


def render_insights(insights_json: str) -> None:
    """
    Render business insights.

    Args:
        insights_json: JSON string with summary and insight bullets.
    """
    if not insights_json:
        return

    try:
        insights = json.loads(insights_json)
    except json.JSONDecodeError:
        return

    insight_bullets = insights.get("insights", [])
    if not insight_bullets:
        return

    st.markdown("### 💡 Insights")

    for bullet in insight_bullets:
        st.markdown(f"- {bullet}")
