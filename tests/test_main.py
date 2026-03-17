"""
Tests for the main routes (e.g. index page).
Uses the client fixture from tests/conftest.py.

Run: 
1. Run all tests in this file with verbose output
python -m pytest tests/test_main.py -v
2. Run only the test_index_returns_200 test with verbose output
python -m pytest tests/test_main.py::test_index_returns_200 -v
"""


def test_index_returns_200(client):
    """GET / should return HTTP 200."""
    rv = client.get("/")
    assert rv.status_code == 200


def test_index_returns_index_page(client):
    """GET / should return the index page with 'Welcome to DailyDose'."""
    rv = client.get("/")
    assert b"Welcome to DailyDose" in rv.data
