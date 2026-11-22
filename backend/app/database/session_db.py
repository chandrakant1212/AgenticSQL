"""
Session dataset manager for in-memory CSV analysis.

Maintains ephemeral SQLite databases for uploaded files per session.
"""

import io
import logging
import re
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine

logger = logging.getLogger(__name__)

class SessionDatabaseManager:
    """Manages in-memory SQLite databases for user sessions."""
    
    def __init__(self):
        # Maps session_id to an active SQLAlchemy Engine (SQLite memory)
        self._engines: dict[str, Engine] = {}
        # Maps session_id to metadata about the uploaded datasets
        self._metadata: dict[str, dict[str, Any]] = {}

    def upload_csv(self, session_id: str, filename: str, content: bytes) -> dict[str, Any]:
        """
        Parse CSV, create an in-memory SQLite engine for the session, 
        and load the data into a table.
        """
        table_name = self._sanitize_table_name(filename)
        
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
            
        # Clean columns
        df.columns = [re.sub(r'[^a-z0-9_]', '_', col.strip().lower()) for col in df.columns]
        df.columns = [f"col_{col}" if col and col[0].isdigit() else col for col in df.columns]

        # Get or create engine for this session
        if session_id not in self._engines:
            # unique shared in-memory database URI per session
            uri = f"sqlite:///file:{session_id}?mode=memory&cache=shared&uri=true"
            self._engines[session_id] = create_engine(uri, connect_args={'check_same_thread': False})
            self._metadata[session_id] = {"tables": []}
            logger.info("Created new in-memory SQLite engine for session: %s", session_id)
            
        engine = self._engines[session_id]

        # Drop ALL previous tables in this session so only the current dataset is active
        from sqlalchemy import inspect, text
        try:
            inspector = inspect(engine)
            for old_tbl in inspector.get_table_names():
                with engine.begin() as conn:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{old_tbl}"'))
            logger.info("Dropped previous session tables for session: %s", session_id)
        except Exception as e:
            logger.warning("Could not drop previous tables: %s", e)
        
        # Load new data
        df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
        
        # Reset metadata with only the new active table
        self._metadata[session_id] = {"tables": [table_name], "active_table": table_name}
        
        logger.info("Loaded %d rows into ephemeral table %s for session %s", len(df), table_name, session_id)
        
        return {
            "table_name": table_name,
            "rows": len(df),
            "columns": list(df.columns)
        }
        
    def get_engine(self, session_id: str) -> Engine | None:
        """Get the ephemeral engine for a session, if it exists."""
        return self._engines.get(session_id)
        
    def clear_session(self, session_id: str) -> None:
        """Clear the ephemeral database for a session."""
        if session_id in self._engines:
            engine = self._engines.pop(session_id)
            from sqlalchemy import inspect, text
            try:
                inspector = inspect(engine)
                for old_tbl in inspector.get_table_names():
                    with engine.begin() as conn:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{old_tbl}"'))
            except Exception as e:
                logger.warning("Could not drop tables on clear: %s", e)
            engine.dispose()
        self._metadata.pop(session_id, None)
        logger.info("Cleared ephemeral database for session: %s", session_id)
        
    def _sanitize_table_name(self, filename: str) -> str:
        """Convert a filename to a valid table name."""
        name = filename.rsplit(".", 1)[0]
        name = name.lower()
        name = re.sub(r'[^a-z0-9]', '_', name)
        name = re.sub(r'^[0-9]+', '', name)
        if not name or name == '_':
            name = "uploaded_dataset"
        return name

# Singleton
_session_db_manager = SessionDatabaseManager()

def get_session_db_manager() -> SessionDatabaseManager:
    return _session_db_manager
