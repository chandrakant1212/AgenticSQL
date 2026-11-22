"""
Test fixtures and configuration.
"""

import os
import sys
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables before importing app modules
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/agenticsql")
os.environ.setdefault("DATABASE_URL_READONLY", "postgresql+psycopg2://postgres:postgres@localhost:5432/agenticsql")


@pytest.fixture
def sample_schema_text():
    """Sample schema text for testing."""
    return """Table: customers
Columns:
  - customer_id: INTEGER [PRIMARY KEY] (NOT NULL)
  - name: VARCHAR(200) (NOT NULL)
  - email: VARCHAR(255) (NOT NULL)
  - country: VARCHAR(100) (NOT NULL)
  - city: VARCHAR(100) (NOT NULL)
  - signup_date: DATE (NOT NULL)

Table: products
Columns:
  - product_id: INTEGER [PRIMARY KEY] (NOT NULL)
  - product_name: VARCHAR(300) (NOT NULL)
  - category: VARCHAR(100) (NOT NULL)
  - price: NUMERIC(10, 2) (NOT NULL)
  - cost: NUMERIC(10, 2) (NOT NULL)

Table: orders
Columns:
  - order_id: INTEGER [PRIMARY KEY] (NOT NULL)
  - customer_id: INTEGER (NOT NULL)
  - order_date: DATE (NOT NULL)
  - status: VARCHAR(50) (NOT NULL)
  - total_amount: NUMERIC(12, 2) (NOT NULL)
Foreign Keys:
  - customer_id → customers.customer_id

Table: order_items
Columns:
  - order_item_id: INTEGER [PRIMARY KEY] (NOT NULL)
  - order_id: INTEGER (NOT NULL)
  - product_id: INTEGER (NOT NULL)
  - quantity: INTEGER (NOT NULL)
  - unit_price: NUMERIC(10, 2) (NOT NULL)
Foreign Keys:
  - order_id → orders.order_id
  - product_id → products.product_id"""


@pytest.fixture
def sample_dataframe_data():
    """Sample DataFrame data for testing."""
    return {
        "columns": ["product_name", "revenue"],
        "data": [
            {"product_name": "Widget A", "revenue": 150000.00},
            {"product_name": "Widget B", "revenue": 120000.00},
            {"product_name": "Widget C", "revenue": 98000.00},
            {"product_name": "Widget D", "revenue": 75000.00},
            {"product_name": "Widget E", "revenue": 62000.00},
        ],
        "dtypes": {"product_name": "object", "revenue": "float64"},
        "shape": [5, 2],
    }
