"""
AgenticSQL — AI Data Analyst

Main Streamlit application providing a clean, professional interface
for natural language data analysis.
"""

import json
import uuid

import streamlit as st

from api_client import AgenticSQLClient
from components.chat import render_chat_input
from components.history import render_history_sidebar
from components.query_details import render_insights, render_query_details
from components.visualization import render_visualization
from components.dataset import render_dataset_upload

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AgenticSQL — AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Answer box */
    .answer-box {
        background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.08) 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Status badges */
    .status-success { color: #22C55E; }
    .status-corrected { color: #F97316; }
    .status-failed { color: #EF4444; }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.5);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    /* Metric styling */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 8px;
        padding: 0.75rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
    }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

if "current_result" not in st.session_state:
    st.session_state["current_result"] = None

# API client
client = AgenticSQLClient()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

# Connection status
with st.sidebar:
    st.markdown("## 🤖 AgenticSQL")
    st.markdown("---")

    health = client.get_health()
    api_status = health.get("status", "unreachable")
    db_status = health.get("database", "unknown")

    if api_status == "unreachable":
        st.error("🔴 Backend Unreachable")
        st.caption("Start the backend from `backend/`: `uvicorn app.main:app --reload`")
    elif db_status == "healthy":
        st.success("🟢 Backend Connected")
    else:
        st.warning("🟡 Backend Online (Database Offline)")
        st.caption("PostgreSQL is not running on port 5432. Run `docker compose up -d postgres`.")

    st.markdown("---")

    # Render history sidebar
    history_index = render_history_sidebar(st.session_state["query_history"])
    
    st.markdown("---")
    
    # Render dataset uploader
    render_dataset_upload(client)

    # If a history item was clicked, show that result
    if history_index is not None and history_index < len(st.session_state["messages"]):
        st.session_state["current_result"] = st.session_state["messages"][history_index]

# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

# Header
st.markdown('<div class="main-header">AgenticSQL</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">AI-Powered Data Analyst — Ask questions about your business data</div>',
    unsafe_allow_html=True,
)

# Chat input
question = render_chat_input()

# Process question
if question:
    with st.spinner("🤖 Analyzing your question..."):
        try:
            result = client.query(
                question=question,
                session_id=st.session_state["session_id"],
            )

            # Store in session state
            st.session_state["messages"].append(result)
            st.session_state["current_result"] = result
            st.session_state["query_history"].append({
                "question": question,
                "status": result.get("status", ""),
                "execution_time": result.get("execution_time", 0),
                "retry_count": result.get("retry_count", 0),
                "timestamp": "",  # Will be filled by server
            })

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.caption("Make sure the backend is running.")

# ---------------------------------------------------------------------------
# Display Current Result
# ---------------------------------------------------------------------------

result = st.session_state.get("current_result")

if result:
    st.markdown("---")

    # Answer
    answer = result.get("answer", "")
    if answer:
        st.markdown("### 🎯 Answer")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

    # Visualization
    chart_json = result.get("chart_json", "")
    if chart_json:
        render_visualization(chart_json)

    # Insights
    insights = result.get("insights", "")
    if insights:
        render_insights(insights)

    # Query details
    render_query_details(result)

elif not st.session_state.get("messages"):
    # Welcome state
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 0; color: #64748B;">
            <h3>👋 Welcome to AgenticSQL</h3>
            <p>Ask any question about your business data — customers, products, orders, and payments.</p>
            <p>The AI agent will automatically generate SQL, execute it, and present insights with visualizations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature highlights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            #### 🧠 Smart SQL
            Automatically generates optimized PostgreSQL queries from your questions.
            """
        )
    with col2:
        st.markdown(
            """
            #### 🔄 Self-Correcting
            Detects and fixes SQL errors automatically with up to 3 retry attempts.
            """
        )
    with col3:
        st.markdown(
            """
            #### 📊 Auto Visualization
            Selects the best chart type and generates interactive Plotly charts.
            """
        )
