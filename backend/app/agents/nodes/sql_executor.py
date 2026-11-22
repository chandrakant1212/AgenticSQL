"""
SQL Executor node.

Executes validated SQL against the read-only PostgreSQL connection.
Captures results, errors, and execution time.
"""

import logging
import time
from typing import Any

import pandas as pd
from sqlalchemy import text

from app.config import get_settings
from app.database.connection import readonly_session

logger = logging.getLogger(__name__)


def sql_executor_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Execute SQL against the database.

    Updates state with:
    - query_result: list[dict] (raw results)
    - dataframe: serialized DataFrame data
    - columns: list of column names
    - execution_time: float (seconds)
    - sql_error: str (if execution failed)
    - retry_count: int (incremented on error)
    """
    sql = state.get("validated_sql") or state.get("generated_sql", "")
    retry_count = state.get("retry_count", 0)
    settings = get_settings()

    logger.info("Executing SQL (attempt %d): %s", retry_count + 1, sql[:200])

    start_time = time.time()

    try:
        session_id = state.get("session_id", "default")
        from app.database.session_db import get_session_db_manager
        db_mgr = get_session_db_manager()
        session_engine = db_mgr.get_engine(session_id)
        
        if session_engine is not None:
            from sqlalchemy.orm import Session
            db_context = Session(session_engine)
        else:
            db_context = readonly_session()

        with db_context as session:
            result = session.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchmany(settings.MAX_RESULT_ROWS)
            total_count = len(rows)

            # Convert to list of dicts
            query_result = [dict(zip(columns, row)) for row in rows]

            execution_time = time.time() - start_time

            logger.info(
                "SQL execution successful: %d rows in %.2fs",
                total_count, execution_time,
            )

            # Create DataFrame for analysis
            df = pd.DataFrame(query_result)

            # Serialize DataFrame data for state
            df_data = {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "shape": list(df.shape),
            }

            return {
                "query_result": query_result,
                "dataframe": df_data,
                "columns": columns,
                "execution_time": execution_time,
                "sql_error": "",
                "total_rows": total_count,
            }

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)

        logger.error(
            "SQL execution failed (attempt %d): %s",
            retry_count + 1, error_msg,
        )

        return {
            "sql_error": error_msg,
            "execution_time": execution_time,
            "retry_count": retry_count + 1,
        }
