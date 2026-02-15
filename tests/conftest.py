

import pytest

from app import app as flask_app

from app import db

@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    return flask_app

@pytest.fixture
def app_context(app):
    """Push application context and create tables"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()


@pytest.fixture
def client(app, app_context):
    """Test client (ensures tables exist via app_context)."""
    return app.test_client()


