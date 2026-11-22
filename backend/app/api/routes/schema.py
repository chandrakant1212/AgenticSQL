"""
Schema API endpoint.

GET /api/schema — Return database schema information.
"""

import logging

from fastapi import APIRouter

from app.api.schemas import SchemaResponse, SchemaTableInfo
from app.database.schema_inspector import SchemaInspector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["schema"])


@router.get("/schema", response_model=SchemaResponse)
async def get_schema() -> SchemaResponse:
    """Return the complete database schema information."""
    inspector = SchemaInspector()
    full_schema = inspector.get_full_schema()
    relationships = inspector.get_relationships()

    tables = []
    for table_name, schema in full_schema.items():
        tables.append(SchemaTableInfo(
            table_name=schema["table_name"],
            columns=schema["columns"],
            primary_keys=schema["primary_keys"],
            foreign_keys=schema["foreign_keys"],
        ))

    return SchemaResponse(
        tables=tables,
        relationships=relationships,
    )
