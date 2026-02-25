# noqa: D100
from __future__ import annotations

from datetime import date, datetime, timezone

import sqlalchemy as sa
import sqlalchemy.orm as so

from app import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Schedule(db.Model):
    """Medication plan: one per dependent."""

    __tablename__ = "schedule"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("user.id"), nullable=False, unique=True, index=True
    )
    name: so.Mapped[str | None] = so.mapped_column(sa.String(120), nullable=True)
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean(), nullable=False, default=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    prescriptions: so.Mapped[list["Prescription"]] = so.relationship(
        "Prescription",
        back_populates="schedule",
        lazy="selectin",
        order_by="Prescription.id",
    )


class Prescription(db.Model):
    """Prescription: one per prescribing event, with multiple medications."""

    __tablename__ = "prescription"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    schedule_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("schedule.id"), nullable=False, index=True
    )
    name: so.Mapped[str | None] = so.mapped_column(sa.String(120), nullable=True)
    prescribed_at: so.Mapped[date | None] = so.mapped_column(sa.Date(), nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    schedule: so.Mapped["Schedule"] = so.relationship("Schedule", back_populates="prescriptions")
    medications: so.Mapped[list["Medication"]] = so.relationship(
        "Medication",
        back_populates="prescription",
        lazy="selectin",
        order_by="Medication.id",
    )


class Medication(db.Model):
    """Medication item: belongs to a prescription; name, dosage, daily times, etc."""

    __tablename__ = "medication"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    prescription_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("prescription.id"), nullable=False, index=True
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False)
    dosage: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    scheduled_times: so.Mapped[list[str]] = so.mapped_column(sa.JSON(), nullable=False)
    instructions: so.Mapped[str | None] = so.mapped_column(sa.String(500), nullable=True)
    start_date: so.Mapped[date | None] = so.mapped_column(sa.Date(), nullable=True)
    duration_days: so.Mapped[int | None] = so.mapped_column(sa.Integer(), nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow
    )

    prescription: so.Mapped["Prescription"] = so.relationship(
        "Prescription", back_populates="medications"
    )
