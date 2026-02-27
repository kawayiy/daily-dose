from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms.schedule import MedicationEditForm, MedicationForm, PrescriptionForm
from app.models.users import User
from app.services.carer_dependent_service import CarerDependentService
from app.services.schedule_service import ScheduleService

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


def _build_prescription_choices(prescriptions):
    choices = [("", "New prescription and add")]
    for p in prescriptions:
        label = p.name if p.name else f"Prescription #{p.id}"
        choices.append((str(p.id), label))
    return choices


def _parse_times(s: str) -> list[str]:
    if not s or not s.strip():
        return []
    return [t.strip() for t in s.split(",") if t.strip()]


def _carer_can_access_dependent(dependent_id: int) -> bool:
    return any(d.id == dependent_id for d in current_user.dependents)


@carer_bp.route("/dependents/<int:dependent_id>/schedule", methods=["GET"])
@login_required
def dependent_schedule(dependent_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    dependent_name = dependent.name if dependent else f"User #{dependent_id}"

    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    schedule_data = ScheduleService.get_daily_schedule(schedule.id)

    return render_template(
        "schedule/plan.html",
        schedule_data=schedule_data,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
        ScheduleService=ScheduleService
    )


@carer_bp.route("/dependents/<int:dependent_id>/prescription/new", methods=["GET", "POST"])
@login_required
def prescription_new(dependent_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    dependent_name = dependent.name if dependent else f"User #{dependent_id}"

    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    prescription_form = PrescriptionForm()

    if request.method == "POST":
        prescription_form = PrescriptionForm(request.form)
        if prescription_form.validate_on_submit():
            ScheduleService.create_prescription(
                schedule.id,
                name=prescription_form.name.data or None,
                prescribed_at=prescription_form.prescribed_at.data,
            )
            flash("Prescription created")
            return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))

    return render_template(
        "schedule/prescription_new.html",
        prescription_form=prescription_form,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
    )


@carer_bp.route("/dependents/<int:dependent_id>/medication/add", methods=["GET", "POST"])
@login_required
def medication_add(dependent_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    dependent_name = dependent.name if dependent else f"User #{dependent_id}"

    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    prescriptions = ScheduleService.get_prescriptions_for_schedule(schedule.id)
    medication_form = MedicationForm()
    medication_form.prescription_id.choices = _build_prescription_choices(prescriptions)

    if request.method == "POST":
        medication_form = MedicationForm(request.form)
        medication_form.prescription_id.choices = _build_prescription_choices(
            ScheduleService.get_prescriptions_for_schedule(schedule.id)
        )
        if medication_form.validate_on_submit():
            prescription_id = medication_form.prescription_id.data
            if prescription_id is None:
                new_p = ScheduleService.create_prescription(schedule.id)
                prescription_id = new_p.id
            times = _parse_times(medication_form.scheduled_times.data or "")
            ok, msg = ScheduleService.validate_input(
                medication_form.name.data or "",
                medication_form.dosage.data or "",
                times,
            )
            if not ok:
                flash(msg)
                return redirect(url_for("carer.medication_add", dependent_id=dependent_id))
            success = ScheduleService.add_medication(
                prescription_id,
                name=medication_form.name.data,
                dosage=medication_form.dosage.data,
                scheduled_times=times,
                instructions=medication_form.instructions.data or None,
                start_date=medication_form.start_date.data,
                duration_days=medication_form.duration_days.data,
            )
            if success:
                flash("Medication saved")
                return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))
            flash("Save failed, please try again")

    prescriptions = ScheduleService.get_prescriptions_for_schedule(schedule.id)
    medication_form.prescription_id.choices = _build_prescription_choices(prescriptions)

    return render_template(
        "schedule/medication_add.html",
        medication_form=medication_form,
        prescriptions=prescriptions,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
    )


@carer_bp.route("/dependents/<int:dependent_id>/prescription/<int:prescription_id>/edit", methods=["GET", "POST"])
@login_required
def prescription_edit(dependent_id: int, prescription_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    dependent_name = dependent.name if dependent else f"User #{dependent_id}"
    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    prescription = ScheduleService.get_prescription_by_schedule(prescription_id, schedule.id)
    if prescription is None:
        flash("Prescription not found")
        return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))

    form = PrescriptionForm()
    if request.method == "GET":
        form.name.data = prescription.name
        form.prescribed_at.data = prescription.prescribed_at
    if request.method == "POST":
        form = PrescriptionForm(request.form)
        if form.validate_on_submit():
            if ScheduleService.update_prescription(
                prescription_id,
                schedule.id,
                name=form.name.data or None,
                prescribed_at=form.prescribed_at.data,
            ):
                flash("Prescription updated")
                return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))
            flash("Update failed")
    form.submit.label.text = "Save"
    return render_template(
        "schedule/prescription_edit.html",
        prescription_form=form,
        prescription_id=prescription_id,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
    )


@carer_bp.route("/dependents/<int:dependent_id>/prescription/<int:prescription_id>/delete", methods=["POST"])
@login_required
def prescription_delete(dependent_id: int, prescription_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))
    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    if ScheduleService.delete_prescription(prescription_id, schedule.id):
        flash("Prescription deleted")
    else:
        flash("Prescription not found")
    return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))


@carer_bp.route("/dependents/<int:dependent_id>/medication/<int:medication_id>/edit", methods=["GET", "POST"])
@login_required
def medication_edit(dependent_id: int, medication_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    dependent_name = dependent.name if dependent else f"User #{dependent_id}"
    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    medication = ScheduleService.get_medication_by_schedule(medication_id, schedule.id)
    if medication is None:
        flash("Medication not found")
        return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))

    form = MedicationEditForm()
    if request.method == "GET":
        form.name.data = medication.name
        form.dosage.data = medication.dosage
        form.scheduled_times.data = ", ".join(medication.scheduled_times)
        form.instructions.data = medication.instructions
        form.start_date.data = medication.start_date
        form.duration_days.data = medication.duration_days
    if request.method == "POST":
        form = MedicationEditForm(request.form)
        if form.validate_on_submit():
            times = _parse_times(form.scheduled_times.data or "")
            ok, msg = ScheduleService.validate_input(
                form.name.data or "", form.dosage.data or "", times
            )
            if not ok:
                flash(msg)
            elif ScheduleService.update_medication(
                medication_id,
                schedule.id,
                name=form.name.data,
                dosage=form.dosage.data,
                scheduled_times=times,
                instructions=form.instructions.data or None,
                start_date=form.start_date.data,
                duration_days=form.duration_days.data,
            ):
                flash("Medication updated")
                return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))
            else:
                flash("Update failed")

    return render_template(
        "schedule/medication_edit.html",
        medication_form=form,
        medication_id=medication_id,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
    )


@carer_bp.route("/dependents/<int:dependent_id>/medication/<int:medication_id>/delete", methods=["POST"])
@login_required
def medication_delete(dependent_id: int, medication_id: int):
    try:
        _require_carer()
    except PermissionError:
        flash("Carers only")
        return redirect(url_for("main.index"))
    if not _carer_can_access_dependent(dependent_id):
        flash("Not allowed to view this dependent's medication plan")
        return redirect(url_for("carer.dependents_list"))
    schedule = ScheduleService.get_or_create_schedule(dependent_id)
    if ScheduleService.delete_medication(medication_id, schedule.id):
        flash("Medication deleted")
    else:
        flash("Medication not found")
    return redirect(url_for("carer.dependent_schedule", dependent_id=dependent_id))

@carer_bp.route("/dependents/<int:dependent_id>/report")
@login_required
def adherence_report(dependent_id: int):
    _require_carer()
    if not _carer_can_access_dependent(dependent_id):
        flash("Access denied")
        return redirect(url_for("carer.dependents_list"))

    dependent = db.session.get(User, dependent_id)
    report_data, percentage = ScheduleService.get_weekly_adherence_report(dependent_id)

    return render_template(
        "carer/report.html",
        dependent=dependent,
        report_data=report_data,
        percentage=percentage
    )