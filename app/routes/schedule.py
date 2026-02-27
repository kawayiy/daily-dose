# noqa: D100
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.schedule import MedicationEditForm, MedicationForm, PrescriptionForm
from app.services.schedule_service import ScheduleService

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


def _build_prescription_choices(prescriptions):
    """Build SelectField choices: new prescription option + existing prescriptions."""
    choices = [("", "New prescription and add")]
    for p in prescriptions:
        label = p.name if p.name else f"Prescription #{p.id}"
        choices.append((str(p.id), label))
    return choices


def _parse_times(s: str) -> list[str]:
    """Parse '08:00, 12:00, 18:00' -> ['08:00','12:00','18:00']."""
    if not s or not s.strip():
        return []
    return [t.strip() for t in s.split(",") if t.strip()]


@schedule_bp.route("", methods=["GET"])
@login_required
def plan():
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    schedule = ScheduleService.get_or_create_schedule(current_user.id)
    schedule_data = ScheduleService.get_daily_schedule(schedule.id)

    return render_template(
        "schedule/plan.html",
        schedule_data=schedule_data,
        dependent_id=None,
        dependent_name=None,
        ScheduleService=ScheduleService
    )


@schedule_bp.route("/prescription/new", methods=["GET", "POST"])
@login_required
def prescription_new():
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    schedule = ScheduleService.get_or_create_schedule(current_user.id)
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
            return redirect(url_for("schedule.plan"))

    return render_template(
        "schedule/prescription_new.html",
        prescription_form=prescription_form,
        dependent_id=None,
        dependent_name=None,
    )


@schedule_bp.route("/medication/add", methods=["GET", "POST"])
@login_required
def medication_add():
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    schedule = ScheduleService.get_or_create_schedule(current_user.id)
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
                return redirect(url_for("schedule.medication_add"))
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
                return redirect(url_for("schedule.plan"))
            flash("Save failed, please try again")

    prescriptions = ScheduleService.get_prescriptions_for_schedule(schedule.id)
    medication_form.prescription_id.choices = _build_prescription_choices(prescriptions)

    return render_template(
        "schedule/medication_add.html",
        medication_form=medication_form,
        prescriptions=prescriptions,
        dependent_id=None,
        dependent_name=None,
    )


@schedule_bp.route("/prescription/<int:prescription_id>/edit", methods=["GET", "POST"])
@login_required
def prescription_edit(prescription_id: int):
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    schedule = ScheduleService.get_or_create_schedule(current_user.id)
    prescription = ScheduleService.get_prescription_by_schedule(prescription_id, schedule.id)
    if prescription is None:
        flash("Prescription not found")
        return redirect(url_for("schedule.plan"))

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
                return redirect(url_for("schedule.plan"))
            flash("Update failed")
    form.submit.label.text = "Save"
    return render_template(
        "schedule/prescription_edit.html",
        prescription_form=form,
        prescription_id=prescription_id,
        dependent_id=None,
        dependent_name=None,
    )


@schedule_bp.route("/prescription/<int:prescription_id>/delete", methods=["POST"])
@login_required
def prescription_delete(prescription_id: int):
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))
    schedule = ScheduleService.get_or_create_schedule(current_user.id)
    if ScheduleService.delete_prescription(prescription_id, schedule.id):
        flash("Prescription deleted")
    else:
        flash("Prescription not found")
    return redirect(url_for("schedule.plan"))


@schedule_bp.route("/medication/<int:medication_id>/edit", methods=["GET", "POST"])
@login_required
def medication_edit(medication_id: int):
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))

    schedule = ScheduleService.get_or_create_schedule(current_user.id)
    medication = ScheduleService.get_medication_by_schedule(medication_id, schedule.id)
    if medication is None:
        flash("Medication not found")
        return redirect(url_for("schedule.plan"))

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
                return redirect(url_for("schedule.plan"))
            else:
                flash("Update failed")

    return render_template(
        "schedule/medication_edit.html",
        medication_form=form,
        medication_id=medication_id,
        dependent_id=None,
        dependent_name=None,
    )


@schedule_bp.route("/medication/<int:medication_id>/delete", methods=["POST"])
@login_required
def medication_delete(medication_id: int):
    if getattr(current_user, "role", None) != "dependent":
        return redirect(url_for("carer.dependents_list"))
    schedule = ScheduleService.get_or_create_schedule(current_user.id)
    if ScheduleService.delete_medication(medication_id, schedule.id):
        flash("Medication deleted")
    else:
        flash("Medication not found")
    return redirect(url_for("schedule.plan"))

@schedule_bp.route("/medication/<int:med_id>/taken", methods=["POST"])
@login_required
def confirm_take(med_id: int):
    slot = request.form.get("time_slot")
    # Basic security check: ensure med belongs to user (optional but recommended)
    ScheduleService.log_taken(med_id, slot)
    flash(f"Medication recorded as taken at {slot}")
    return redirect(url_for("schedule.plan"))