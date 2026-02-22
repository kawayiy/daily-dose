from __future__ import annotations

from app import db
from app.models.users import User
import sqlalchemy as sa


class CarerDependentService:
    @staticmethod
    def _get_user(user_id: int) -> User:
        user = db.session.get(User, int(user_id))
        if not user:
            raise ValueError("User not found")
        return user

    @staticmethod
    def list_dependents(carer_id: int) -> list[User]:
        carer = CarerDependentService._get_user(carer_id)
        if not carer.is_carer():
            raise PermissionError("Not a carer")
        return list(carer.dependents)

    @staticmethod
    def list_available_dependents(carer_id: int) -> list[User]:
        carer = CarerDependentService._get_user(carer_id)
        if not carer.is_carer():
            raise PermissionError("Not a carer")

        linked_ids = {u.id for u in carer.dependents}
        candidates = User.query.filter_by(role=User.ROLE_DEPENDENT).all()
        return [u for u in candidates if u.id not in linked_ids]

    @staticmethod
    def add_link(carer_id: int, dependent_id: int) -> None:
        if int(carer_id) == int(dependent_id):
            raise ValueError("Cannot link to self")

        carer = CarerDependentService._get_user(carer_id)
        dependent = CarerDependentService._get_user(dependent_id)

        if not carer.is_carer():
            raise PermissionError("Not a carer")
        if not dependent.is_dependent():
            raise ValueError("Target user is not a dependent")

        if dependent in carer.dependents:
            return

        carer.dependents.append(dependent)
        db.session.commit()

    @staticmethod
    def remove_link(carer_id: int, dependent_id: int) -> None:
        carer = CarerDependentService._get_user(carer_id)
        if not carer.is_carer():
            raise PermissionError("Not a carer")

        dependent = CarerDependentService._get_user(dependent_id)
        if dependent in carer.dependents:
            carer.dependents.remove(dependent)
            db.session.commit()
    


    @staticmethod
    def search_available_dependents_by_email(carer_id: int, q: str) -> list[User]:
        carer = CarerDependentService._get_user(carer_id)
        if not carer.is_carer():
            raise PermissionError("Not a carer")

        q = (q or "").strip().lower()
        linked_ids = {u.id for u in carer.dependents}

        query = User.query.filter(User.role == User.ROLE_DEPENDENT)
        if q:
            query = query.filter(sa.func.lower(User.email).contains(q))

        results = query.all()
        return [u for u in results if u.id not in linked_ids]