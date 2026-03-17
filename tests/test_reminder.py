"""
Tests for reminder-related ScheduleService logic.
Uses app_context from tests/conftest.py.

Run:
  python -m pytest tests/test_reminder.py -v
"""

from datetime import datetime, timezone

import pytest

from app import db
from app.models.schedule import Medication, MedicationLog
from app.models.users import User
from app.services import schedule_service as schedule_service_module
from app.services.schedule_service import ScheduleService


@pytest.fixture
def dependent_user(clean_db):
    """Create a dependent user for reminder tests."""
    user = User(
        name="Reminder Test User",
        email="reminder-test@example.com",
        password_hash="x",
        role=User.ROLE_DEPENDENT,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def schedule(dependent_user):
    """Create a schedule for the dependent user."""
    return ScheduleService.get_or_create_schedule(dependent_user.id)


def test_log_taken_creates_medication_log(app_context, schedule):
    """log_taken creates a MedicationLog for the medication and slot."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Reminder Rx")
    ScheduleService.add_medication(prescription.id, "Aspirin", "100mg", ["08:00"])
    medication = db.session.execute(
        db.select(Medication).where(Medication.prescription_id == prescription.id)
    ).scalar_one()

    ScheduleService.log_taken(medication.id, "08:00")

    logs = db.session.execute(
        db.select(MedicationLog).where(MedicationLog.medication_id == medication.id)
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].scheduled_time_slot == "08:00"
    assert logs[0].taken_at is not None


def test_get_pending_alerts_returns_due_slots_not_logged_today(app_context, schedule, dependent_user, monkeypatch):
    """get_pending_alerts returns medication slots up to the current time when not logged today."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Reminder Rx")
    ScheduleService.add_medication(
        prescription.id,
        "Vitamin D",
        "1 tablet",
        ["08:00", "12:00", "18:00"],
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 2, 24, 12, 30, 0)

    monkeypatch.setattr(schedule_service_module, "datetime", FixedDateTime)

    pending = ScheduleService.get_pending_alerts(dependent_user.id)

    assert len(pending) == 2
    assert pending[0]["name"] == "Vitamin D"
    assert pending[0]["slot"] == "08:00"
    assert pending[1]["slot"] == "12:00"


def test_get_pending_alerts_skips_logged_slots_for_today(app_context, schedule, dependent_user, monkeypatch):
    """get_pending_alerts excludes a slot when it already has a log for today."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Reminder Rx")
    ScheduleService.add_medication(prescription.id, "Ibuprofen", "200mg", ["08:00", "20:00"])
    medication = db.session.execute(
        db.select(Medication).where(Medication.prescription_id == prescription.id)
    ).scalar_one()

    db.session.add(
        MedicationLog(
            medication_id=medication.id,
            scheduled_time_slot="08:00",
            taken_at=datetime(2025, 2, 24, 8, 5, 0, tzinfo=timezone.utc),
        )
    )
    db.session.commit()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 2, 24, 21, 0, 0)

    monkeypatch.setattr(schedule_service_module, "datetime", FixedDateTime)

    pending = ScheduleService.get_pending_alerts(dependent_user.id)

    assert len(pending) == 1
    assert pending[0]["name"] == "Ibuprofen"
    assert pending[0]["slot"] == "20:00"
