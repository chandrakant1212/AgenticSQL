"""
Unit tests for visualization chart selection.
"""

import pandas as pd
import pytest

from app.agents.nodes.visualizer import _heuristic_chart_selection


class TestVisualization:
    """Tests for the visualization heuristic fallback."""

    def test_single_metric(self):
        """Single-value result should produce a metric chart."""
        df = pd.DataFrame({"total_revenue": [2430000.00]})
        column_types = {"total_revenue": "numeric"}
        config = _heuristic_chart_selection(df, df.columns.tolist(), column_types, "total revenue")
        assert config["chart_type"] == "metric"

    def test_time_series(self):
        """Time + numeric data should produce a line chart."""
        df = pd.DataFrame({
            "month": pd.to_datetime(["2025-01", "2025-02", "2025-03"]),
            "revenue": [100000, 120000, 115000],
        })
        column_types = {"month": "datetime", "revenue": "numeric"}
        config = _heuristic_chart_selection(df, df.columns.tolist(), column_types, "monthly revenue")
        assert config["chart_type"] == "line"

    def test_category_comparison_small(self):
        """Small category comparison should produce a bar chart."""
        df = pd.DataFrame({
            "category": ["Electronics", "Clothing", "Books"],
            "revenue": [500000, 300000, 100000],
        })
        column_types = {"category": "categorical", "revenue": "numeric"}
        config = _heuristic_chart_selection(df, df.columns.tolist(), column_types, "revenue by category")
        assert config["chart_type"] == "bar"

    def test_ranking_large(self):
        """Large ranking should produce a horizontal bar chart."""
        df = pd.DataFrame({
            "product": [f"Product {i}" for i in range(15)],
            "revenue": list(range(15000, 0, -1000)),
        })
        column_types = {"product": "categorical", "revenue": "numeric"}
        config = _heuristic_chart_selection(df, df.columns.tolist(), column_types, "top products")
        assert config["chart_type"] == "horizontal_bar"

    def test_no_numeric_columns(self):
        """Non-numeric data should produce a table."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "email": ["a@b.com", "b@c.com"],
        })
        column_types = {"name": "categorical", "email": "categorical"}
        config = _heuristic_chart_selection(df, df.columns.tolist(), column_types, "customers")
        assert config["chart_type"] == "table"


class TestChartGenerator:
    """Tests for the Plotly chart generator."""

    def test_bar_chart_generation(self):
        """Test that a bar chart can be generated."""
        from app.services.chart_generator import generate_chart

        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "revenue": [100, 200, 300],
        })
        config = {
            "chart_type": "bar",
            "x_axis": "category",
            "y_axis": "revenue",
            "title": "Test Bar Chart",
        }

        chart_json = generate_chart(df, config)
        assert chart_json  # Not empty
        assert "data" in chart_json
        assert "layout" in chart_json

    def test_line_chart_generation(self):
        """Test that a line chart can be generated."""
        from app.services.chart_generator import generate_chart

        df = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar"],
            "revenue": [100, 200, 150],
        })
        config = {
            "chart_type": "line",
            "x_axis": "month",
            "y_axis": "revenue",
            "title": "Test Line Chart",
        }

        chart_json = generate_chart(df, config)
        assert chart_json

    def test_invalid_column_fallback(self):
        """Test that invalid columns fallback gracefully."""
        from app.services.chart_generator import generate_chart

        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })
        config = {
            "chart_type": "bar",
            "x_axis": "nonexistent",
            "y_axis": "also_nonexistent",
            "title": "Fallback Test",
        }

        chart_json = generate_chart(df, config)
        assert chart_json  # Should not crash
