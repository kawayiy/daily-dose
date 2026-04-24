"""Tests for schedule plan page rendering."""

import pytest

from app import db
from app.services.user_service import UserService


@pytest.fixture
def dependent_user(clean_db):
    """Create a dependent user for schedule plan tests."""
    return UserService.register(
        name="Plan Dependent",
        email="plan-dependent@example.com",
        password="pass456",
        role="dependent",
    )


@pytest.fixture
def carer_user(clean_db):
    """Create a carer user for schedule plan tests."""
    return UserService.register(
        name="Plan Carer",
        email="plan-carer@example.com",
        password="pass123",
        role="carer",
    )


def test_schedule_plan_includes_minute_refresh_for_dependent(client, dependent_user):
    """Dependent schedule page includes the minute auto-refresh hook."""
    client.post(
        "/login",
        data={"email": dependent_user.email, "password": "pass456", "remember": "n"},
        follow_redirects=True,
    )

    rv = client.get("/schedule")

    assert rv.status_code == 200
    assert b"dd-plan-auto-refresh" in rv.data
    assert b"window.location.reload()" in rv.data


def test_schedule_plan_includes_minute_refresh_for_carer_view(client, carer_user, dependent_user):
    """Carer dependent schedule page includes the same minute auto-refresh hook."""
    carer_user.dependents.append(dependent_user)
    db.session.commit()

    client.post(
        "/login",
        data={"email": carer_user.email, "password": "pass123", "remember": "n"},
        follow_redirects=True,
    )

    rv = client.get(f"/carer/dependents/{dependent_user.id}/schedule")

    assert rv.status_code == 200
    assert b"dd-plan-auto-refresh" in rv.data
    assert b"window.location.reload()" in rv.data
