"""
Database schema introspection.

Dynamically inspects the PostgreSQL database to retrieve:
- Table names
- Column names, data types, nullability
- Primary keys
- Foreign keys and relationships

This information is provided to the LLM for SQL generation.
"""

import logging
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.database.connection import get_admin_engine

logger = logging.getLogger(__name__)


class SchemaInspector:
    """Inspects database schema for LLM context."""

    def __init__(self, engine: Engine | None = None):
        self._engine = engine or get_admin_engine()

    def get_all_tables(self) -> list[str]:
        """Return a list of all user table names in the database."""
        inspector = inspect(self._engine)
        tables = inspector.get_table_names()
        logger.debug("Found %d tables: %s", len(tables), tables)
        return tables

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """
        Return detailed schema information for a single table.

        Returns:
            {
                "table_name": str,
                "columns": [
                    {
                        "name": str,
                        "type": str,
                        "nullable": bool,
                        "primary_key": bool,
                    },
                    ...
                ],
                "primary_keys": [str],
                "foreign_keys": [
                    {
                        "column": str,
                        "references_table": str,
                        "references_column": str,
                    },
                    ...
                ],
            }
        """
        inspector = inspect(self._engine)

        # Columns
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "primary_key": False,  # will be updated below
            })

        # Primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint.get("constrained_columns", [])
        for col in columns:
            if col["name"] in pk_columns:
                col["primary_key"] = True

        # Foreign keys
        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            for i, col in enumerate(fk["constrained_columns"]):
                foreign_keys.append({
                    "column": col,
                    "references_table": fk["referred_table"],
                    "references_column": fk["referred_columns"][i],
                })

        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": pk_columns,
            "foreign_keys": foreign_keys,
        }

    def get_full_schema(self) -> dict[str, dict[str, Any]]:
        """Return schema information for all tables."""
        tables = self.get_all_tables()
        schema = {}
        for table in tables:
            schema[table] = self.get_table_schema(table)
        return schema

    def get_relationships(self) -> list[dict[str, str]]:
        """
        Return all foreign key relationships in the database.

        Returns:
            [
                {
                    "from_table": str,
                    "from_column": str,
                    "to_table": str,
                    "to_column": str,
                },
                ...
            ]
        """
        relationships = []
        for table in self.get_all_tables():
            schema = self.get_table_schema(table)
            for fk in schema["foreign_keys"]:
                relationships.append({
                    "from_table": table,
                    "from_column": fk["column"],
                    "to_table": fk["references_table"],
                    "to_column": fk["references_column"],
                })
        return relationships

    def get_tables_schema_text(self, table_names: list[str]) -> str:
        """
        Return a human-readable schema description for the given tables.

        This is the primary method used to build LLM context.
        Only includes the specified tables to reduce token usage.
        """
        parts = []
        all_relationships = self.get_relationships()

        for table_name in table_names:
            try:
                schema = self.get_table_schema(table_name)
            except Exception as e:
                logger.warning("Could not inspect table '%s': %s", table_name, e)
                continue

            lines = [f"Table: {schema['table_name']}"]
            lines.append("Columns:")
            for col in schema["columns"]:
                pk_marker = " [PRIMARY KEY]" if col["primary_key"] else ""
                null_marker = " (nullable)" if col["nullable"] else " (NOT NULL)"
                lines.append(
                    f"  - {col['name']}: {col['type']}{pk_marker}{null_marker}"
                )

            # Foreign keys relevant to this table
            relevant_fks = [
                r for r in all_relationships
                if r["from_table"] == table_name
            ]
            if relevant_fks:
                lines.append("Foreign Keys:")
                for fk in relevant_fks:
                    lines.append(
                        f"  - {fk['from_column']} → {fk['to_table']}.{fk['to_column']}"
                    )

            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    def get_table_descriptions(self) -> dict[str, str]:
        """
        Return brief descriptions for each table based on column names.

        Used by the query planner to select relevant tables.
        """
        descriptions = {}
        for table in self.get_all_tables():
            schema = self.get_table_schema(table)
            col_names = [c["name"] for c in schema["columns"]]
            descriptions[table] = (
                f"Table '{table}' with columns: {', '.join(col_names)}"
            )
        return descriptions

    def get_sample_values(self, table_name: str, column_name: str, limit: int = 5) -> list[str]:
        """
        Return sample distinct values for a column.

        Useful for helping the LLM understand categorical data.
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(
                    text(
                        f"SELECT DISTINCT {column_name} FROM {table_name} "
                        f"WHERE {column_name} IS NOT NULL LIMIT :limit"
                    ),
                    {"limit": limit},
                )
                return [str(row[0]) for row in result]
        except Exception as e:
            logger.warning(
                "Could not get sample values for %s.%s: %s",
                table_name, column_name, e,
            )
            return []
