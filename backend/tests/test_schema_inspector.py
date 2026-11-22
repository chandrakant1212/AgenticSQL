"""
Unit tests for the schema inspector.

These tests require a running PostgreSQL database with seeded data.
"""

import pytest


class TestSchemaInspector:
    """Tests for the SchemaInspector class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the schema inspector."""
        try:
            from app.database.schema_inspector import SchemaInspector
            self.inspector = SchemaInspector()
            self._available = True
        except Exception:
            self._available = False

    @pytest.mark.skipif(
        not True, reason="Requires database connection"
    )
    def test_get_all_tables(self):
        """Test that all expected tables are discovered."""
        if not self._available:
            pytest.skip("Database not available")

        tables = self.inspector.get_all_tables()
        expected = {"customers", "products", "orders", "order_items", "payments"}
        assert expected.issubset(set(tables)), f"Missing tables: {expected - set(tables)}"

    def test_get_table_schema(self):
        """Test schema retrieval for a single table."""
        if not self._available:
            pytest.skip("Database not available")

        schema = self.inspector.get_table_schema("customers")
        assert schema["table_name"] == "customers"
        assert len(schema["columns"]) > 0

        col_names = [c["name"] for c in schema["columns"]]
        assert "customer_id" in col_names
        assert "name" in col_names
        assert "email" in col_names
        assert "country" in col_names

    def test_get_primary_keys(self):
        """Test that primary keys are correctly identified."""
        if not self._available:
            pytest.skip("Database not available")

        schema = self.inspector.get_table_schema("customers")
        assert "customer_id" in schema["primary_keys"]

    def test_get_foreign_keys(self):
        """Test foreign key detection."""
        if not self._available:
            pytest.skip("Database not available")

        schema = self.inspector.get_table_schema("orders")
        fk_columns = [fk["column"] for fk in schema["foreign_keys"]]
        assert "customer_id" in fk_columns

    def test_get_relationships(self):
        """Test that relationships are discovered."""
        if not self._available:
            pytest.skip("Database not available")

        relationships = self.inspector.get_relationships()
        assert len(relationships) > 0

        # Check for known relationships
        rel_pairs = [(r["from_table"], r["to_table"]) for r in relationships]
        assert ("orders", "customers") in rel_pairs
        assert ("order_items", "orders") in rel_pairs
        assert ("order_items", "products") in rel_pairs

    def test_get_tables_schema_text(self):
        """Test text-format schema generation."""
        if not self._available:
            pytest.skip("Database not available")

        text = self.inspector.get_tables_schema_text(["customers", "orders"])
        assert "customers" in text
        assert "orders" in text
        assert "customer_id" in text

    def test_get_table_descriptions(self):
        """Test table description generation."""
        if not self._available:
            pytest.skip("Database not available")

        descriptions = self.inspector.get_table_descriptions()
        assert "customers" in descriptions
        assert "products" in descriptions
        assert "customer_id" in descriptions["customers"]
