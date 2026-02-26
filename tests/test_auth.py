"""
Tests for auth routes: login, register, logout.
Uses client, app_context, clean_db from tests/conftest.py.
CSRF is disabled in test app so POST data does not need csrf_token.

Run:
  python -m pytest tests/test_auth.py -v
"""

import pytest

from app import db
from app.models.users import User
from app.services.user_service import UserService


@pytest.fixture
def registered_carer(clean_db):
    """A carer user already in DB (password: pass123)."""
    return UserService.register(
        name="Test Carer",
        email="carer@example.com",
        password="pass123",
        role=User.ROLE_CARER,
    )


@pytest.fixture
def registered_dependent(clean_db):
    """A dependent user already in DB (password: pass456)."""
    return UserService.register(
        name="Test Dependent",
        email="dependent@example.com",
        password="pass456",
        role=User.ROLE_DEPENDENT,
    )


# --- Login GET ---


def test_login_get_returns_200(client):
    """GET /login returns 200 and shows login form."""
    rv = client.get("/login")
    assert rv.status_code == 200
    assert b"Login" in rv.data
    assert b"email" in rv.data.lower() or b"Email" in rv.data


def test_login_get_shows_register_link(client):
    """GET /login page contains link to register."""
    rv = client.get("/login")
    assert rv.status_code == 200
    assert b"Register" in rv.data or b"register" in rv.data


# --- Login POST ---


def test_login_success_dependent_redirects_to_plan(client, registered_dependent):
    """POST /login with valid dependent credentials redirects to schedule plan."""
    rv = client.post(
        "/login",
        data={
            "email": "dependent@example.com",
            "password": "pass456",
            "remember": "n",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert "/schedule" in rv.location or "plan" in rv.location or rv.location.endswith("/schedule/plan")
    # Follow and check flash
    rv2 = client.post(
        "/login",
        data={"email": "dependent@example.com", "password": "pass456", "remember": "n"},
        follow_redirects=True,
    )
    assert b"Logged in" in rv2.data or b"schedule" in rv2.data.lower()


def test_login_success_carer_redirects_to_dependents(client, registered_carer):
    """POST /login with valid carer credentials redirects to carer dependents list."""
    rv = client.post(
        "/login",
        data={
            "email": "carer@example.com",
            "password": "pass123",
            "remember": "n",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert "carer" in rv.location or "dependents" in rv.location


def test_login_invalid_password_shows_message(client, registered_dependent):
    """POST /login with wrong password shows error and re-renders form."""
    rv = client.post(
        "/login",
        data={
            "email": "dependent@example.com",
            "password": "wrong",
            "remember": "n",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Invalid email or password" in rv.data
    assert b"Login" in rv.data


def test_login_unknown_email_shows_message(client):
    """POST /login with non-existent email shows error."""
    rv = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "any", "remember": "n"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Invalid email or password" in rv.data


# --- Register GET ---


def test_register_get_returns_200(client):
    """GET /register returns 200 and shows register form."""
    rv = client.get("/register")
    assert rv.status_code == 200
    assert b"Register" in rv.data
    assert b"password" in rv.data.lower() or b"Password" in rv.data
    assert b"role" in rv.data.lower() or b"Role" in rv.data


def test_register_get_shows_login_link(client):
    """GET /register page contains link to login."""
    rv = client.get("/register")
    assert rv.status_code == 200
    assert b"Login" in rv.data or b"login" in rv.data


# --- Register POST ---


def test_register_success_redirects_and_logs_in(client, clean_db):
    """POST /register with valid data creates user, redirects to index, and logs in."""
    rv = client.post(
        "/register",
        data={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "secure123",
            "password_confirm": "secure123",
            "role": User.ROLE_DEPENDENT,
            "phone": "",
            "age": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Registered" in rv.data or b"Welcome" in rv.data
    # User exists in DB
    user = UserService.get_user_by_email("newuser@example.com")
    assert user is not None
    assert user.name == "New User"
    assert user.role == User.ROLE_DEPENDENT


def test_register_duplicate_email_shows_flash(client, clean_db):
    """POST /register with already registered email shows error and re-renders form."""
    UserService.register("First", "same@example.com", "pass", User.ROLE_DEPENDENT)
    rv = client.post(
        "/register",
        data={
            "name": "Second",
            "email": "same@example.com",
            "password": "other123",
            "password_confirm": "other123",
            "role": User.ROLE_CARER,
            "phone": "",
            "age": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Email already registered" in rv.data
    # Only one user with that email
    count = User.query.filter_by(email="same@example.com").count()
    assert count == 1


def test_register_password_mismatch_rejects(client, clean_db):
    """POST /register with password != password_confirm re-renders form (validation error)."""
    rv = client.post(
        "/register",
        data={
            "name": "User",
            "email": "mismatch@example.com",
            "password": "pass123",
            "password_confirm": "pass456",
            "role": User.ROLE_DEPENDENT,
            "phone": "",
            "age": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert UserService.get_user_by_email("mismatch@example.com") is None


# --- Logout ---


def test_logout_post_redirects_and_logs_out(client, registered_dependent):
    """POST /logout when logged in redirects to index and logs out."""
    client.post(
        "/login",
        data={"email": "dependent@example.com", "password": "pass456", "remember": "n"},
        follow_redirects=True,
    )
    rv = client.post("/logout", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Logged out" in rv.data or b"Welcome" in rv.data
    # Accessing protected route should redirect to login
    rv2 = client.get("/schedule", follow_redirects=False)
    assert rv2.status_code == 302
    assert "login" in rv2.location


def test_logout_without_login_redirects_to_login(client):
    """POST /logout when not logged in redirects to login (login_required)."""
    rv = client.post("/logout", follow_redirects=False)
    assert rv.status_code == 302
    assert "login" in rv.location


# --- Protected route redirect ---


def test_protected_route_redirects_to_login_when_anonymous(client):
    """GET a protected route (e.g. /schedule) when not logged in redirects to /login."""
    rv = client.get("/schedule", follow_redirects=False)
    assert rv.status_code == 302
    assert "login" in rv.location
