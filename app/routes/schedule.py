from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


@schedule_bp.route("")
@login_required
def plan():
    
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    return render_template("schedule/plan.html")