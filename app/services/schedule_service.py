# noqa: D100
"""Schedule / Prescription / Medication business logic."""
from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import sqlalchemy as sa
from app import db
from app.models.schedule import Medication, Prescription, Schedule

if TYPE_CHECKING:
    pass

# HH:MM or H:MM
_TIME_PATTERN = re.compile(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class ScheduleService:
    """Schedule, prescription and medication creation, validation and queries."""

    @staticmethod
    def get_or_create_schedule(user_id: int) -> Schedule:
        """Return existing schedule for user or create and return one."""
        schedule = db.session.execute(
            db.select(Schedule).where(Schedule.user_id == user_id)
        ).scalar_one_or_none()
        if schedule is not None:
            return schedule
        schedule = Schedule(user_id=user_id, name=None, is_active=True)
        db.session.add(schedule)
        db.session.commit()
        return schedule

    @staticmethod
    def create_prescription(
        schedule_id: int,
        name: str | None = None,
        prescribed_at: date | None = None,
    ) -> Prescription:
        """Create a new prescription."""
        prescription = Prescription(
            schedule_id=schedule_id,
            name=name or None,
            prescribed_at=prescribed_at,
        )
        db.session.add(prescription)
        db.session.commit()
        return prescription

    @staticmethod
    def validate_input(name: str, dosage: str, times: list[str]) -> tuple[bool, str]:
        """Validate medication name, dosage and time list. Returns (ok, error_message)."""
        name = (name or "").strip()
        dosage = (dosage or "").strip()
        if not name:
            return False, "Medication name is required"
        if len(name) > 200:
            return False, "Medication name too long"
        if not dosage:
            return False, "Dosage is required"
        if len(dosage) > 100:
            return False, "Dosage too long"
        if not times:
            return False, "Enter at least one time"
        for t in times:
            t = (t or "").strip()
            if not t:
                return False, "Time cannot be empty"
            if not _TIME_PATTERN.match(t):
                return False, f"Invalid time format (use HH:MM): {t!r}"
        return True, ""

    @staticmethod
    def add_medication(
        prescription_id: int,
        name: str,
        dosage: str,
        scheduled_times: list[str],
        instructions: str | None = None,
        start_date: date | None = None,
        duration_days: int | None = None,
    ) -> bool:
        """Add medication under the given prescription. Returns True on success."""
        ok, msg = ScheduleService.validate_input(name, dosage, scheduled_times)
        if not ok:
            return False
        try:
            # Normalize times to HH:MM
            normalized = []
            for t in scheduled_times:
                t = (t or "").strip()
                if t:
                    normalized.append(t)
            if not normalized:
                return False
            med = Medication(
                prescription_id=prescription_id,
                name=name.strip(),
                dosage=dosage.strip(),
                scheduled_times=normalized,
                instructions=(instructions or "").strip() or None,
                start_date=start_date,
                duration_days=duration_days,
            )
            db.session.add(med)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_daily_schedule(schedule_id: int) -> list[dict]:
        """Return prescriptions and medications for this schedule, grouped by prescription."""
        schedule = db.session.get(Schedule, schedule_id)
        if schedule is None:
            return []
        if not schedule.is_active:
            return []
        result = []
        for p in schedule.prescriptions:
            medications = [
                {
                    "id": m.id,
                    "name": m.name,
                    "dosage": m.dosage,
                    "scheduled_times": m.scheduled_times,
                    "instructions": m.instructions,
                    "start_date": m.start_date.isoformat() if m.start_date else None,
                    "duration_days": m.duration_days,
                }
                for m in p.medications
            ]
            result.append(
                {
                    "prescription_id": p.id,
                    "name": p.name,
                    "prescribed_at": p.prescribed_at.isoformat() if p.prescribed_at else None,
                    "medications": medications,
                }
            )
        return result

    @staticmethod
    def get_prescriptions_for_schedule(schedule_id: int) -> list[Prescription]:
        """Return all prescriptions for this schedule (for medication form dropdown)."""
        return (
            db.session.execute(
                db.select(Prescription).where(Prescription.schedule_id == schedule_id).order_by(Prescription.id)
            )
            .scalars()
            .all()
        )

    @staticmethod
    def get_prescription_by_schedule(prescription_id: int, schedule_id: int) -> Prescription | None:
        """Return prescription if it belongs to the given schedule."""
        p = db.session.get(Prescription, prescription_id)
        if p is None or p.schedule_id != schedule_id:
            return None
        return p

    @staticmethod
    def get_medication_by_schedule(medication_id: int, schedule_id: int) -> Medication | None:
        """Return medication if its prescription belongs to the given schedule."""
        m = db.session.get(Medication, medication_id)
        if m is None or m.prescription.schedule_id != schedule_id:
            return None
        return m

    @staticmethod
    def update_prescription(
        prescription_id: int,
        schedule_id: int,
        name: str | None = None,
        prescribed_at: date | None = None,
    ) -> bool:
        """Update prescription; returns True if it belongs to schedule and update succeeded."""
        p = ScheduleService.get_prescription_by_schedule(prescription_id, schedule_id)
        if p is None:
            return False
        try:
            if name is not None:
                p.name = name.strip() or None
            if prescribed_at is not None:
                p.prescribed_at = prescribed_at
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def delete_prescription(prescription_id: int, schedule_id: int) -> bool:
        """Delete prescription and its medications; returns True if it belonged to schedule."""
        p = ScheduleService.get_prescription_by_schedule(prescription_id, schedule_id)
        if p is None:
            return False
        try:
            for m in list(p.medications):
                db.session.delete(m)
            db.session.delete(p)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def update_medication(
        medication_id: int,
        schedule_id: int,
        name: str,
        dosage: str,
        scheduled_times: list[str],
        instructions: str | None = None,
        start_date: date | None = None,
        duration_days: int | None = None,
    ) -> bool:
        """Update medication; returns True if it belongs to schedule and validation/update succeeded."""
        m = ScheduleService.get_medication_by_schedule(medication_id, schedule_id)
        if m is None:
            return False
        ok, msg = ScheduleService.validate_input(name, dosage, scheduled_times)
        if not ok:
            return False
        try:
            normalized = [t.strip() for t in scheduled_times if (t or "").strip()]
            if not normalized:
                return False
            m.name = name.strip()
            m.dosage = dosage.strip()
            m.scheduled_times = normalized
            m.instructions = (instructions or "").strip() or None
            m.start_date = start_date
            m.duration_days = duration_days
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def delete_medication(medication_id: int, schedule_id: int) -> bool:
        """Delete medication; returns True if it belonged to schedule."""
        m = ScheduleService.get_medication_by_schedule(medication_id, schedule_id)
        if m is None:
            return False
        try:
            db.session.delete(m)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False


    @staticmethod
    def get_pending_alerts(user_id: int):
        """Find medications due in the last 2 hours that haven't been logged today."""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_date = now.date()

        schedule = ScheduleService.get_or_create_schedule(user_id)
        pending = []

        for prescription in schedule.prescriptions:
            for med in prescription.medications:
                for slot in med.scheduled_times:
                    # Logic: If slot <= current_time AND no log exists for today
                    if slot <= current_time_str:
                        exists = db.session.execute(
                            db.select(MedicationLog).where(
                                MedicationLog.medication_id == med.id,
                                MedicationLog.scheduled_time_slot == slot,
                                sa.func.date(MedicationLog.taken_at) == today_date
                            )
                        ).scalar_one_or_none()

                        if not exists:
                            pending.append({
                                "med_id": med.id,
                                "name": med.name,
                                "dosage": med.dosage,
                                "slot": slot
                            })
        return pending

    @staticmethod
    def log_taken(medication_id: int, slot: str):
        """Record that a medication has been taken."""
        log = MedicationLog(medication_id=medication_id, scheduled_time_slot=slot)
        db.session.add(log)
        db.session.commit()


    @staticmethod
    def get_weekly_adherence_report(user_id: int):
        now = datetime.now()
        start_date = (now - timedelta(days=6)).date()
        schedule = ScheduleService.get_or_create_schedule(user_id)

        report = []
        total_expected = 0
        total_taken = 0

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            # Use a dictionary to group by prescription
            day_data = {"date": current_date, "prescriptions": {}}

            for prescription in schedule.prescriptions:
                p_name = prescription.name or f"Prescription #{prescription.id}"

                for med in prescription.medications:
                    # Basic check for start_date
                    if med.start_date and med.start_date > current_date:
                        continue

                    for slot in med.scheduled_times:
                        total_expected += 1
                        log = db.session.execute(
                            db.select(MedicationLog).where(
                                MedicationLog.medication_id == med.id,
                                MedicationLog.scheduled_time_slot == slot,
                                sa.func.date(MedicationLog.taken_at) == current_date
                            )
                        ).scalar_one_or_none()

                        is_taken = log is not None
                        if is_taken: total_taken += 1

                        if p_name not in day_data["prescriptions"]:
                            day_data["prescriptions"][p_name] = []

                        day_data["prescriptions"][p_name].append({
                            "med_name": med.name,
                            "slot": slot,
                            "taken": is_taken,
                            "taken_at": log.taken_at if is_taken else None
                        })
            report.append(day_data)

        percentage = (total_taken / total_expected * 100) if total_expected > 0 else 100
        return sorted(report, key=lambda x: x['date'], reverse=True), round(percentage, 1)


