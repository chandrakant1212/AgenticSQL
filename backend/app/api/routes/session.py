"""
Session API endpoint.

POST /api/session/upload — Upload a CSV file into the session's ephemeral database.
DELETE /api/session — Clear session data.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.database.session_db import get_session_db_manager
from app.services.conversation import get_conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/upload")
async def upload_ephemeral_dataset(
    session_id: str = Form(...),
    file: UploadFile = File(...)
) -> dict:
    """
    Upload a CSV file into an ephemeral in-memory database for the session.
    This does NOT permanently modify the PostgreSQL database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    logger.info("Uploading ephemeral dataset %s for session %s", file.filename, session_id)

    try:
        content = await file.read()
        db_mgr = get_session_db_manager()
        result = db_mgr.upload_csv(session_id, file.filename, content)
        
        # Clear prior conversation history so the LLM focuses on the newly uploaded dataset
        conversation_mgr = get_conversation_manager()
        conversation_mgr.clear(session_id)
        
        return {
            "message": f"Successfully loaded {result['rows']} rows to memory as '{result['table_name']}'.",
            "table_name": result['table_name'],
            "rows": result['rows'],
            "columns": result['columns']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to upload dataset: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")


@router.delete("")
async def clear_session(session_id: str) -> dict:
    """Clear conversation history and ephemeral databases for a session."""
    # Clear conversation
    conversation_mgr = get_conversation_manager()
    conversation_mgr.clear(session_id)
    
    # Clear ephemeral db
    db_mgr = get_session_db_manager()
    db_mgr.clear_session(session_id)
    
    return {"message": "Session cleared", "session_id": session_id}
