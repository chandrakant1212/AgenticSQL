"""
Dataset upload component for the Streamlit UI sidebar.
"""

import streamlit as st

from api_client import AgenticSQLClient


def render_dataset_upload(client: AgenticSQLClient) -> None:
    """
    Render a file uploader to upload CSV datasets.
    Automatically uploads and ingests the CSV into the session database
    as soon as a file is dropped or selected.
    
    Args:
        client: The API client.
    """
    st.markdown("## 📁 Upload Dataset")
    
    uploaded_file = st.file_uploader(
        "Upload a CSV file to query it.",
        type=["csv"],
        help="The file will be analyzed temporarily in memory for this session.",
        key="dataset_file_uploader",
    )
    
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # Only upload if this file hasn't been uploaded yet in this session
        if st.session_state.get("uploaded_dataset_id") != file_id:
            with st.status(f"Analyzing and loading `{uploaded_file.name}`...", expanded=True) as status:
                try:
                    file_bytes = uploaded_file.getvalue()
                    session_id = st.session_state.get("session_id", "default")
                    response = client.upload_dataset(session_id, uploaded_file.name, file_bytes)
                    
                    table_name = response.get("table_name", "dataset")
                    rows = response.get("rows", 0)
                    
                    st.session_state["uploaded_dataset_id"] = file_id
                    st.session_state["active_table_name"] = table_name
                    st.session_state["active_table_rows"] = rows
                    
                    # Clear old messages and query history from previous datasets
                    st.session_state["messages"] = []
                    st.session_state["query_history"] = []
                    st.session_state["current_result"] = None
                    
                    status.update(label="Dataset loaded successfully!", state="complete", expanded=False)
                    st.success(f"✅ Active table: `{table_name}` ({rows} rows)")
                    
                    # Store a message so the user knows they can query it
                    st.session_state["messages"].append({
                        "answer": f"Dataset `{uploaded_file.name}` loaded successfully! Created table `{table_name}` with {rows} rows. You can now ask questions about this data in the chat.",
                        "status": "success",
                        "sql": "",
                        "execution_time": 0,
                    })
                    st.rerun()
                    
                except Exception as e:
                    status.update(label="Upload failed", state="error")
                    st.error(f"Failed to upload: {str(e)}")
        else:
            table_name = st.session_state.get("active_table_name", "dataset")
            rows = st.session_state.get("active_table_rows", 0)
            st.success(f"✅ Active table: `{table_name}` ({rows} rows)")
    else:
        # Reset if file was removed
        if "uploaded_dataset_id" in st.session_state:
            del st.session_state["uploaded_dataset_id"]
            try:
                session_id = st.session_state.get("session_id", "default")
                client.clear_session(session_id)
            except Exception:
                pass
        if "active_table_name" in st.session_state:
            del st.session_state["active_table_name"]
        if "active_table_rows" in st.session_state:
            del st.session_state["active_table_rows"]

