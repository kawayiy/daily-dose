
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin

from app import db


def utcnow():
    return datetime.now(timezone.utc)


carer_dependent = sa.Table(
    "carer_dependent",
    db.metadata,
    sa.Column("carer_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("dependent_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=utcnow),
)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    ROLE_CARER = "carer"
    ROLE_DEPENDENT = "dependent"
    ROLE_CHOICES = {ROLE_CARER, ROLE_DEPENDENT}

    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    name: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    password_hash: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)

    role: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=False, index=True)

    phone: so.Mapped[str | None] = so.mapped_column(sa.String(20), nullable=True)
    age: so.Mapped[int | None] = so.mapped_column(sa.Integer, nullable=True)

    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    dependents: so.Mapped[list["User"]] = so.relationship(
        "User",
        secondary=carer_dependent,
        primaryjoin=lambda: User.id == carer_dependent.c.carer_id,
        secondaryjoin=lambda: User.id == carer_dependent.c.dependent_id,
        back_populates="carers",
        lazy="selectin",
    )

    carers: so.Mapped[list["User"]] = so.relationship(
        "User",
        secondary=carer_dependent,
        primaryjoin=lambda: User.id == carer_dependent.c.dependent_id,
        secondaryjoin=lambda: User.id == carer_dependent.c.carer_id,
        back_populates="dependents",
        lazy="selectin",
    )

    def is_carer(self) -> bool:
        return self.role == self.ROLE_CARER

    def is_dependent(self) -> bool:
        return self.role == self.ROLE_DEPENDENT