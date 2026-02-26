"""
Tests for ScheduleService: prescription and medication logic.
Uses app_context from tests/conftest.py.

Run:
  python -m pytest tests/test_schedule_service.py -v
"""

from datetime import date

import pytest

from app import db
from app.models.schedule import Medication, Prescription, Schedule
from app.models.users import User
from app.services.schedule_service import ScheduleService


@pytest.fixture
def dependent_user(clean_db):
    """Create a dependent user and return it. clean_db clears tables before each test so fixed emails are fine."""
    user = User(
        name="Test Dependent",
        email="dependent-schedule-test@example.com",
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


# --- Prescription ---


def test_get_or_create_schedule_creates_once(app_context, dependent_user):
    """get_or_create_schedule creates one schedule per user and returns it."""
    s1 = ScheduleService.get_or_create_schedule(dependent_user.id)
    s2 = ScheduleService.get_or_create_schedule(dependent_user.id)
    assert s1.id is not None
    assert s1.user_id == dependent_user.id
    assert s1.id == s2.id


def test_create_prescription_returns_prescription_with_id(app_context, schedule):
    """create_prescription returns a Prescription with id and optional name/date."""
    p = ScheduleService.create_prescription(schedule.id, name="Cardiology", prescribed_at=date(2025, 2, 24))
    assert p.id is not None
    assert p.schedule_id == schedule.id
    assert p.name == "Cardiology"
    assert p.prescribed_at == date(2025, 2, 24)


def test_create_prescription_without_name_and_date(app_context, schedule):
    """create_prescription works with no name or prescribed_at."""
    p = ScheduleService.create_prescription(schedule.id)
    assert p.id is not None
    assert p.name is None
    assert p.prescribed_at is None


def test_get_prescription_by_schedule_returns_when_belongs(app_context, schedule):
    """get_prescription_by_schedule returns prescription when it belongs to schedule."""
    p = ScheduleService.create_prescription(schedule.id, name="Ortho")
    found = ScheduleService.get_prescription_by_schedule(p.id, schedule.id)
    assert found is not None
    assert found.id == p.id
    assert found.name == "Ortho"


def test_get_prescription_by_schedule_returns_none_for_wrong_schedule(app_context, dependent_user):
    """get_prescription_by_schedule returns None when prescription belongs to another schedule."""
    s1 = ScheduleService.get_or_create_schedule(dependent_user.id)
    p = ScheduleService.create_prescription(s1.id, name="A")
    other_user = User(name="Other", email="other-sched@example.com", password_hash="x", role=User.ROLE_DEPENDENT)
    db.session.add(other_user)
    db.session.commit()
    s2 = ScheduleService.get_or_create_schedule(other_user.id)
    found = ScheduleService.get_prescription_by_schedule(p.id, s2.id)
    assert found is None


def test_update_prescription_updates_name_and_date(app_context, schedule):
    """update_prescription updates name and prescribed_at."""
    p = ScheduleService.create_prescription(schedule.id, name="Old", prescribed_at=date(2025, 1, 1))
    ok = ScheduleService.update_prescription(p.id, schedule.id, name="New", prescribed_at=date(2025, 2, 20))
    assert ok is True
    db.session.refresh(p)
    assert p.name == "New"
    assert p.prescribed_at == date(2025, 2, 20)


def test_update_prescription_returns_false_for_wrong_schedule(app_context, schedule, dependent_user):
    """update_prescription returns False when prescription does not belong to schedule."""
    p = ScheduleService.create_prescription(schedule.id, name="A")
    other_user = User(name="O", email="o-sched@example.com", password_hash="x", role=User.ROLE_DEPENDENT)
    db.session.add(other_user)
    db.session.commit()
    other_schedule = ScheduleService.get_or_create_schedule(other_user.id)
    ok = ScheduleService.update_prescription(p.id, other_schedule.id, name="Hack")
    assert ok is False
    db.session.refresh(p)
    assert p.name == "A"


def test_delete_prescription_removes_prescription_and_medications(app_context, schedule):
    """delete_prescription removes the prescription and its medications."""
    p = ScheduleService.create_prescription(schedule.id, name="ToDelete")
    ScheduleService.add_medication(p.id, "M1", "10mg", ["08:00"])
    ok = ScheduleService.delete_prescription(p.id, schedule.id)
    assert ok is True
    assert db.session.get(Prescription, p.id) is None
    assert len(db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()) == 0


def test_delete_prescription_returns_false_for_wrong_schedule(app_context, schedule):
    """delete_prescription returns False when prescription does not belong to schedule."""
    p = ScheduleService.create_prescription(schedule.id, name="A")
    ok = ScheduleService.delete_prescription(p.id, schedule.id + 999)
    assert ok is False
    assert db.session.get(Prescription, p.id) is not None


# --- Medication: validate_input ---


def test_validate_input_accepts_valid(app_context):
    """validate_input returns (True, '') for valid name, dosage, times."""
    ok, msg = ScheduleService.validate_input("Aspirin", "100mg", ["08:00", "20:00"])
    assert ok is True
    assert msg == ""


def test_validate_input_rejects_empty_name(app_context):
    """validate_input rejects empty medication name."""
    ok, msg = ScheduleService.validate_input("", "10mg", ["08:00"])
    assert ok is False
    assert "name" in msg.lower()


def test_validate_input_rejects_empty_dosage(app_context):
    """validate_input rejects empty dosage."""
    ok, msg = ScheduleService.validate_input("Drug", "", ["08:00"])
    assert ok is False
    assert "dosage" in msg.lower()


def test_validate_input_rejects_empty_times(app_context):
    """validate_input rejects empty times list."""
    ok, msg = ScheduleService.validate_input("Drug", "10mg", [])
    assert ok is False
    assert "time" in msg.lower()


def test_validate_input_rejects_invalid_time_format(app_context):
    """validate_input rejects invalid time format (must be HH:MM)."""
    ok, msg = ScheduleService.validate_input("Drug", "10mg", ["8:00"])  # 8:00 is actually valid per regex
    assert ok is True
    ok, msg = ScheduleService.validate_input("Drug", "10mg", ["25:00"])
    assert ok is False
    ok, msg = ScheduleService.validate_input("Drug", "10mg", ["abc"])
    assert ok is False


# --- Medication: add, get, update, delete ---


def test_add_medication_returns_true_and_persists(app_context, schedule):
    """add_medication returns True and creates a Medication."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ok = ScheduleService.add_medication(p.id, "Aspirin", "100mg", ["08:00", "20:00"], instructions="After meal")
    assert ok is True
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    assert len(meds) == 1
    assert meds[0].name == "Aspirin"
    assert meds[0].dosage == "100mg"
    assert meds[0].scheduled_times == ["08:00", "20:00"]
    assert meds[0].instructions == "After meal"


def test_add_medication_rejects_invalid_and_returns_false(app_context, schedule):
    """add_medication returns False when validation fails."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ok = ScheduleService.add_medication(p.id, "", "10mg", ["08:00"])
    assert ok is False
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    assert len(meds) == 0


def test_get_medication_by_schedule_returns_when_belongs(app_context, schedule):
    """get_medication_by_schedule returns medication when its prescription belongs to schedule."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ScheduleService.add_medication(p.id, "M1", "5mg", ["09:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    found = ScheduleService.get_medication_by_schedule(m.id, schedule.id)
    assert found is not None
    assert found.id == m.id
    assert found.name == "M1"


def test_get_medication_by_schedule_returns_none_for_wrong_schedule(app_context, dependent_user):
    """get_medication_by_schedule returns None when medication belongs to another schedule."""
    s1 = ScheduleService.get_or_create_schedule(dependent_user.id)
    p = ScheduleService.create_prescription(s1.id, name="A")
    ScheduleService.add_medication(p.id, "M1", "1mg", ["08:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    other_user = User(name="O2", email="o2-sched@example.com", password_hash="x", role=User.ROLE_DEPENDENT)
    db.session.add(other_user)
    db.session.commit()
    s2 = ScheduleService.get_or_create_schedule(other_user.id)
    found = ScheduleService.get_medication_by_schedule(m.id, s2.id)
    assert found is None


def test_update_medication_updates_fields(app_context, schedule):
    """update_medication updates name, dosage, times, etc."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ScheduleService.add_medication(p.id, "Old", "5mg", ["08:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    ok = ScheduleService.update_medication(m.id, schedule.id, "New", "10mg", ["09:00", "21:00"], instructions="Updated")
    assert ok is True
    db.session.refresh(m)
    assert m.name == "New"
    assert m.dosage == "10mg"
    assert m.scheduled_times == ["09:00", "21:00"]
    assert m.instructions == "Updated"


def test_update_medication_returns_false_for_invalid_times(app_context, schedule):
    """update_medication returns False when new times fail validation."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ScheduleService.add_medication(p.id, "M", "5mg", ["08:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    ok = ScheduleService.update_medication(m.id, schedule.id, "M", "5mg", [])
    assert ok is False
    db.session.refresh(m)
    assert m.scheduled_times == ["08:00"]


def test_delete_medication_removes_medication(app_context, schedule):
    """delete_medication removes the medication."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ScheduleService.add_medication(p.id, "M1", "5mg", ["08:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    ok = ScheduleService.delete_medication(m.id, schedule.id)
    assert ok is True
    assert db.session.get(Medication, m.id) is None


def test_delete_medication_returns_false_for_wrong_schedule(app_context, schedule):
    """delete_medication returns False when medication does not belong to schedule."""
    p = ScheduleService.create_prescription(schedule.id, name="Rx")
    ScheduleService.add_medication(p.id, "M1", "5mg", ["08:00"])
    meds = db.session.execute(db.select(Medication).where(Medication.prescription_id == p.id)).scalars().all()
    m = meds[0]
    ok = ScheduleService.delete_medication(m.id, schedule.id + 999)
    assert ok is False
    assert db.session.get(Medication, m.id) is not None


# --- get_daily_schedule, get_prescriptions_for_schedule ---


def test_get_daily_schedule_returns_grouped_prescriptions_and_medications(app_context, schedule):
    """get_daily_schedule returns list of prescription blocks with medications."""
    p = ScheduleService.create_prescription(schedule.id, name="Cardiology", prescribed_at=date(2025, 2, 24))
    ScheduleService.add_medication(p.id, "A", "1mg", ["08:00"])
    ScheduleService.add_medication(p.id, "B", "2mg", ["12:00"])
    data = ScheduleService.get_daily_schedule(schedule.id)
    assert len(data) == 1
    assert data[0]["prescription_id"] == p.id
    assert data[0]["name"] == "Cardiology"
    assert data[0]["prescribed_at"] == "2025-02-24"
    assert len(data[0]["medications"]) == 2
    names = [m["name"] for m in data[0]["medications"]]
    assert "A" in names and "B" in names


def test_get_daily_schedule_returns_empty_when_schedule_inactive(app_context, dependent_user):
    """get_daily_schedule returns [] when schedule is_active is False."""
    s = ScheduleService.get_or_create_schedule(dependent_user.id)
    s.is_active = False
    db.session.commit()
    data = ScheduleService.get_daily_schedule(s.id)
    assert data == []


def test_get_prescriptions_for_schedule_returns_ordered_list(app_context, schedule):
    """get_prescriptions_for_schedule returns prescriptions for the schedule in id order."""
    ScheduleService.create_prescription(schedule.id, name="First")
    ScheduleService.create_prescription(schedule.id, name="Second")
    pres = ScheduleService.get_prescriptions_for_schedule(schedule.id)
    assert len(pres) == 2
    assert pres[0].name == "First"
    assert pres[1].name == "Second"
