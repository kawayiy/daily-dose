"""
Tests for the main routes (e.g. index page).
Uses the client fixture from tests/conftest.py.

Run:
  python -m pytest              # full suite
  python -m pytest tests/test_main.py -v   # this file only
"""


def test_index_unauthenticated_redirects_to_login(client):
    """GET / without a session should redirect to the login page."""
    rv = client.get("/", follow_redirects=False)
    assert rv.status_code == 302
    loc = rv.location or ""
    assert "/login" in loc
    assert loc.rstrip("/").endswith("/login")
