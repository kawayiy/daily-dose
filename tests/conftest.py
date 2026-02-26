"""Pytest config. Use a separate DB for tests so development data in instance/app.db is never touched."""

import os

# Use in-memory SQLite for tests (must set before app is imported)
os.environ["DATABASE_URI"] = "sqlite:///:memory:"

import pytest

from app import app as flask_app
from app import db

@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False  # allow POST without CSRF token in tests
    return flask_app

@pytest.fixture
def app_context(app):
    """Push application context and create tables."""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()


@pytest.fixture
def clean_db(app_context):
    """Clear all table data before each test so fixtures can use fixed emails.
    Depends on app_context so tables exist. Delete in FK order: medication -> prescription -> schedule -> carer_dependent -> user, item."""
    from sqlalchemy import text

    from app.models import demo, schedule  # noqa: F401 - register tables

    for table in ("medication", "prescription", "schedule", "carer_dependent", "user", "item"):
        try:
            db.session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass
    db.session.commit()
    yield


@pytest.fixture
def client(app, app_context):
    """Test client (ensures tables exist via app_context)."""
    return app.test_client()


