from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.carer_dependent_service import CarerDependentService

carer_bp = Blueprint("carer", __name__, url_prefix="/carer")


def _require_carer():
    if not getattr(current_user, "role", None) == "carer":
        raise PermissionError("Carer only")


@carer_bp.route("/dependents")
@login_required
def dependents_list():
    try:
        _require_carer()
        dependents = CarerDependentService.list_dependents(current_user.id)
        return render_template("carer/dependents.html", dependents=dependents)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("main.index"))


@carer_bp.route("/dependents/add", methods=["GET", "POST"])
@login_required
def dependents_add():
    _require_carer()

    if request.method == "POST":
        dependent_id = int(request.form["dependent_id"])
        CarerDependentService.add_link(current_user.id, dependent_id)
        flash("Linked")
        return redirect(url_for("carer.dependents_list"))

    q = request.args.get("q", "")
    candidates = CarerDependentService.search_available_dependents_by_email(current_user.id, q)

    return render_template("carer/dependents_add.html", candidates=candidates, q=q)


@carer_bp.route("/dependents/<int:dependent_id>/remove", methods=["POST"])
@login_required
def dependents_remove(dependent_id: int):
    try:
        _require_carer()
        CarerDependentService.remove_link(current_user.id, dependent_id)
        flash("Unlinked")
    except Exception as e:
        flash(str(e))
    return redirect(url_for("carer.dependents_list"))