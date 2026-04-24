"""
Tests for reporting-related ScheduleService logic.
Uses app_context from tests/conftest.py.

Run:
  python -m pytest tests/test_reporting.py -v
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app import db
from app.models.schedule import Medication, MedicationLog
from app.models.users import User
from app.services import schedule_service as schedule_service_module
from app.services.schedule_service import ScheduleService


@pytest.fixture
def dependent_user(clean_db):
    """Create a dependent user for reporting tests."""
    user = User(
        name="Reporting Test User",
        email="reporting-test@example.com",
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


def test_get_weekly_adherence_report_returns_days_and_percentage(app_context, schedule, dependent_user, monkeypatch):
    """get_weekly_adherence_report returns 7 days of data and the expected adherence percentage."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Morning Plan")
    ScheduleService.add_medication(
        prescription.id,
        "Metformin",
        "500mg",
        ["08:00"],
        start_date=date(2025, 2, 18),
    )
    medication = db.session.execute(
        db.select(Medication).where(Medication.prescription_id == prescription.id)
    ).scalar_one()

    db.session.add(
        MedicationLog(
            medication_id=medication.id,
            scheduled_time_slot="08:00",
            taken_at=datetime(2025, 2, 22, 8, 10, 0, tzinfo=timezone.utc),
        )
    )
    db.session.commit()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 2, 24, 10, 0, 0)

    monkeypatch.setattr(schedule_service_module, "datetime", FixedDateTime)

    report_data, percentage = ScheduleService.get_weekly_adherence_report(dependent_user.id)

    assert len(report_data) == 7
    assert report_data[0]["date"] == date(2025, 2, 24)
    assert report_data[-1]["date"] == date(2025, 2, 18)
    assert percentage == 14.3

    day_with_log = next(day for day in report_data if day["date"] == date(2025, 2, 22))
    assert "Morning Plan" in day_with_log["prescriptions"]
    assert day_with_log["prescriptions"]["Morning Plan"][0]["med_name"] == "Metformin"
    assert day_with_log["prescriptions"]["Morning Plan"][0]["taken"] is True

    latest_day = report_data[0]
    assert latest_day["prescriptions"]["Morning Plan"][0]["taken"] is False


def test_get_weekly_adherence_report_skips_days_before_medication_start_date(app_context, schedule, dependent_user, monkeypatch):
    """get_weekly_adherence_report skips medication entries before the medication start date."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Evening Plan")
    ScheduleService.add_medication(
        prescription.id,
        "Calcium",
        "1 tablet",
        ["20:00"],
        start_date=date(2025, 2, 23),
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 2, 24, 21, 0, 0)

    monkeypatch.setattr(schedule_service_module, "datetime", FixedDateTime)

    report_data, percentage = ScheduleService.get_weekly_adherence_report(dependent_user.id)

    latest_day = report_data[0]
    previous_day = report_data[1]
    older_day = next(day for day in report_data if day["date"] == date(2025, 2, 22))

    assert latest_day["date"] == date(2025, 2, 24)
    assert previous_day["date"] == date(2025, 2, 23)
    assert "Evening Plan" in latest_day["prescriptions"]
    assert "Evening Plan" in previous_day["prescriptions"]
    assert older_day["prescriptions"] == {}
    assert percentage == 0.0


def test_get_weekly_adherence_report_converts_taken_time_to_local_display_time(
    app_context, schedule, dependent_user, monkeypatch
):
    """Report timestamps are displayed in local time even when SQLite returns naive UTC values."""
    prescription = ScheduleService.create_prescription(schedule.id, name="Night Plan")
    ScheduleService.add_medication(
        prescription.id,
        "Melatonin",
        "1 tablet",
        ["01:33"],
        start_date=date(2025, 4, 24),
    )
    medication = db.session.execute(
        db.select(Medication).where(Medication.prescription_id == prescription.id)
    ).scalar_one()

    db.session.add(
        MedicationLog(
            medication_id=medication.id,
            scheduled_time_slot="01:33",
            taken_at=datetime(2025, 4, 24, 0, 33, 0, tzinfo=timezone.utc),
        )
    )
    db.session.commit()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 4, 24, 10, 0, 0)

    monkeypatch.setattr(schedule_service_module, "datetime", FixedDateTime)
    monkeypatch.setattr(
        ScheduleService,
        "_get_local_timezone",
        staticmethod(lambda: ZoneInfo("Europe/London")),
    )

    report_data, _ = ScheduleService.get_weekly_adherence_report(dependent_user.id)

    latest_day = report_data[0]
    entry = latest_day["prescriptions"]["Night Plan"][0]

    assert entry["slot"] == "01:33"
    assert entry["taken"] is True
    assert entry["taken_at"].strftime("%H:%M") == "01:33"
