"""
Tests for UserService: get_user_by_email, register, verify_password.
Uses app_context and clean_db from tests/conftest.py.

Run:
  python -m pytest tests/test_user_service.py -v
"""

import pytest

from app import db
from app.models.users import User
from app.services.user_service import UserService


@pytest.fixture
def existing_user(clean_db):
    """Create a user in DB for tests that need one (password is 'secret')."""
    from werkzeug.security import generate_password_hash
    user = User(
        name="Existing User",
        email="existing@example.com",
        password_hash=generate_password_hash("secret"),
        role=User.ROLE_DEPENDENT,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_get_user_by_email_returns_none_when_not_found(app_context):
    """get_user_by_email returns None when email is not in DB."""
    assert UserService.get_user_by_email("nobody@example.com") is None


def test_get_user_by_email_returns_user_when_found(app_context, existing_user):
    """get_user_by_email returns the user when email exists."""
    user = UserService.get_user_by_email("existing@example.com")
    assert user is not None
    assert user.id == existing_user.id
    assert user.email == "existing@example.com"
    assert user.name == "Existing User"


def test_get_user_by_email_normalizes_email(app_context, existing_user):
    """get_user_by_email treats email as case-insensitive and strips whitespace."""
    assert UserService.get_user_by_email("  EXISTING@EXAMPLE.COM  ") is not None
    assert UserService.get_user_by_email("EXISTING@EXAMPLE.COM").id == existing_user.id


def test_register_creates_user(app_context, clean_db):
    """register creates a user with hashed password and returns it."""
    user = UserService.register(
        name="New User",
        email="new@example.com",
        password="password123",
        role=User.ROLE_CARER,
    )
    assert user.id is not None
    assert user.name == "New User"
    assert user.email == "new@example.com"
    assert user.role == User.ROLE_CARER
    assert user.password_hash != "password123"
    assert user.phone is None
    assert user.age is None

    # Persisted
    found = db.session.get(User, user.id)
    assert found is not None
    assert found.email == "new@example.com"


def test_register_with_optional_phone_and_age(app_context, clean_db):
    """register accepts optional phone and age."""
    user = UserService.register(
        name="With Optional",
        email="opt@example.com",
        password="pass",
        role=User.ROLE_DEPENDENT,
        phone="+86 123",
        age=25,
    )
    assert user.phone == "+86 123"
    assert user.age == 25


def test_register_duplicate_email_raises(app_context, clean_db):
    """register raises ValueError when email is already registered."""
    UserService.register("A", "dup@example.com", "pass", User.ROLE_DEPENDENT)
    with pytest.raises(ValueError, match="Email already registered"):
        UserService.register("B", "dup@example.com", "other", User.ROLE_CARER)


def test_register_invalid_role_raises(app_context, clean_db):
    """register raises ValueError when role is invalid."""
    with pytest.raises(ValueError, match="Invalid role"):
        UserService.register("A", "a@example.com", "pass", "admin")


def test_register_invalid_age_raises(app_context, clean_db):
    """register raises ValueError when age is out of range."""
    with pytest.raises(ValueError, match="Invalid age"):
        UserService.register("A", "a@example.com", "pass", User.ROLE_DEPENDENT, age=0)
    with pytest.raises(ValueError, match="Invalid age"):
        UserService.register("A", "b@example.com", "pass", User.ROLE_DEPENDENT, age=121)


def test_verify_password_returns_true_for_correct(app_context, existing_user):
    """verify_password returns True when password matches."""
    assert UserService.verify_password(existing_user, "secret") is True


def test_verify_password_returns_false_for_wrong(app_context, existing_user):
    """verify_password returns False when password does not match."""
    assert UserService.verify_password(existing_user, "wrong") is False
