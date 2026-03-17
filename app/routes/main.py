
from flask import Blueprint, redirect, url_for

from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    if getattr(current_user, "role", None) == "carer":
        return redirect(url_for("carer.dependents_list"))

    return redirect(url_for("schedule.plan"))

