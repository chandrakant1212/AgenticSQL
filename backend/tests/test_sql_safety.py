"""
Unit tests for SQL safety validation.
"""

import pytest

from app.services.sql_safety import validate_sql


class TestSQLSafety:
    """Tests for the SQL safety validation service."""

    # --- Allowed operations ---

    def test_simple_select(self):
        result = validate_sql("SELECT * FROM customers;")
        assert result.is_valid is True

    def test_select_with_where(self):
        result = validate_sql("SELECT name FROM customers WHERE country = 'US';")
        assert result.is_valid is True

    def test_select_with_join(self):
        sql = """
        SELECT c.name, o.total_amount
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id;
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_select_with_group_by(self):
        sql = "SELECT country, COUNT(*) FROM customers GROUP BY country;"
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_select_with_having(self):
        sql = "SELECT country, COUNT(*) as cnt FROM customers GROUP BY country HAVING COUNT(*) > 10;"
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_select_with_order_by(self):
        sql = "SELECT * FROM products ORDER BY price DESC;"
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_select_with_limit(self):
        sql = "SELECT * FROM products LIMIT 5;"
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_select_with_subquery(self):
        sql = """
        SELECT * FROM customers
        WHERE customer_id IN (SELECT customer_id FROM orders);
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_cte_query(self):
        sql = """
        WITH top_customers AS (
            SELECT customer_id, SUM(total_amount) as total
            FROM orders GROUP BY customer_id
        )
        SELECT c.name, tc.total
        FROM top_customers tc
        JOIN customers c ON tc.customer_id = c.customer_id;
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_window_function(self):
        sql = """
        SELECT product_name, price,
               RANK() OVER (PARTITION BY category ORDER BY price DESC) as rank
        FROM products;
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_aggregation_functions(self):
        sql = "SELECT SUM(total_amount), AVG(total_amount), MIN(total_amount), MAX(total_amount) FROM orders;"
        result = validate_sql(sql)
        assert result.is_valid is True

    # --- Blocked operations ---

    def test_block_insert(self):
        result = validate_sql("INSERT INTO customers (name) VALUES ('test');")
        assert result.is_valid is False
        assert "INSERT" in result.reason.upper() or "Blocked" in result.reason

    def test_block_update(self):
        result = validate_sql("UPDATE customers SET name = 'test' WHERE customer_id = 1;")
        assert result.is_valid is False

    def test_block_delete(self):
        result = validate_sql("DELETE FROM customers WHERE customer_id = 1;")
        assert result.is_valid is False

    def test_block_drop_table(self):
        result = validate_sql("DROP TABLE customers;")
        assert result.is_valid is False

    def test_block_alter_table(self):
        result = validate_sql("ALTER TABLE customers ADD COLUMN age INT;")
        assert result.is_valid is False

    def test_block_truncate(self):
        result = validate_sql("TRUNCATE TABLE customers;")
        assert result.is_valid is False

    def test_block_create_table(self):
        result = validate_sql("CREATE TABLE test (id INT PRIMARY KEY);")
        assert result.is_valid is False

    def test_block_grant(self):
        result = validate_sql("GRANT ALL ON customers TO public;")
        assert result.is_valid is False

    # --- Case variations ---

    def test_block_insert_uppercase(self):
        result = validate_sql("INSERT INTO customers (name) VALUES ('test');")
        assert result.is_valid is False

    def test_block_insert_mixed_case(self):
        result = validate_sql("InSeRt INTO customers (name) VALUES ('test');")
        assert result.is_valid is False

    # --- Edge cases ---

    def test_empty_sql(self):
        result = validate_sql("")
        assert result.is_valid is False

    def test_whitespace_only(self):
        result = validate_sql("   ")
        assert result.is_valid is False

    def test_multi_statement_injection(self):
        result = validate_sql("SELECT * FROM customers; DROP TABLE customers;")
        assert result.is_valid is False

    def test_comment_with_injection(self):
        sql = "SELECT * FROM customers; -- DROP TABLE customers"
        result = validate_sql(sql)
        # Should fail because of multi-statement
        assert result.is_valid is False

    def test_select_into(self):
        sql = "SELECT * INTO OUTFILE '/tmp/data' FROM customers;"
        result = validate_sql(sql)
        assert result.is_valid is False
