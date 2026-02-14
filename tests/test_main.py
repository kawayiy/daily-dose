"""
Tests for the main routes (e.g. index page).
使用 tests/conftest.py 中的 client fixture。

Run: python -m pytest tests/test_main.py -v
"""
import pytest


def test_index_returns_200(client):
    """GET / should return HTTP 200."""
    rv = client.get("/")
    assert rv.status_code == 200


def test_index_returns_index_page(client):
    """GET / should return the index page with 'Welcome to DailyDose'."""
    rv = client.get("/")
    assert b"Welcome to DailyDose" in rv.data


def test_demo_db_returns_200(client):
    """GET /demo-db should return HTTP 200."""
    rv = client.get("/demo-db")
    assert rv.status_code == 200


def test_demo_db_returns_json_list(client):
    """GET /demo-db should return a JSON array of items with id and name."""
    rv = client.get("/demo-db")
    data = rv.get_json()
    print("\n/demo-db response:", data)
    assert isinstance(data, list)
    # After this request, at least one item exists (the one just added in demo_db)
    assert len(data) >= 1
    for row in data:
        assert "id" in row and "name" in row
        assert isinstance(row["id"], int)
        assert isinstance(row["name"], str)
