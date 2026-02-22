from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.users import User


class UserService:
    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def register(
        name: str,
        email: str,
        password: str,
        role: str,
        phone: str | None = None,
        age: int | None = None,
    ) -> User:
        role = role.strip().lower()
        if role not in User.ROLE_CHOICES:
            raise ValueError("Invalid role")

        email_norm = email.strip().lower()
        if UserService.get_user_by_email(email_norm):
            raise ValueError("Email already registered")

        if age is not None and not (1 <= int(age) <= 120):
            raise ValueError("Invalid age")

        user = User(
            name=name.strip(),
            email=email_norm,
            password_hash=generate_password_hash(password),
            role=role,
            phone=(phone.strip() if phone else None),
            age=(int(age) if age is not None else None),
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        return check_password_hash(user.password_hash, password)