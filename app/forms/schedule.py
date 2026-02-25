# noqa: D100
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PrescriptionForm(FlaskForm):
    """New prescription form."""

    name = StringField(
        "Prescription name (optional)",
        validators=[Optional(), Length(max=120)],
        description="e.g. Cardiology, Orthopedics",
    )
    prescribed_at = DateField(
        "Prescribed date (optional)",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    submit = SubmitField("Create prescription")


def _coerce_prescription_id(value: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class MedicationForm(FlaskForm):
    """Add medication under a prescription. prescription_id choices are set in the view."""

    prescription_id = SelectField(
        "Prescription",
        validators=[Optional()],  # None = create new prescription then add medication
        coerce=_coerce_prescription_id,
        choices=[],
    )
    name = StringField(
        "Medication name",
        validators=[DataRequired(message="Please enter medication name"), Length(max=200)],
    )
    dosage = StringField(
        "Dosage",
        validators=[DataRequired(message="Please enter dosage"), Length(max=100)],
    )
    scheduled_times = StringField(
        "Times (comma-separated)",
        validators=[DataRequired(message="Enter at least one time, e.g. 08:00, 12:00, 18:00")],
        description="e.g. 08:00, 12:00, 18:00",
    )
    instructions = StringField(
        "Instructions (optional)",
        validators=[Optional(), Length(max=500)],
    )
    start_date = DateField(
        "Start date (optional)",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    duration_days = IntegerField(
        "Duration in days (optional, use with start date)",
        validators=[Optional(), NumberRange(min=1)],
    )
    submit = SubmitField("Save")


class MedicationEditForm(FlaskForm):
    """Edit existing medication (no prescription selector)."""

    name = StringField(
        "Medication name",
        validators=[DataRequired(message="Please enter medication name"), Length(max=200)],
    )
    dosage = StringField(
        "Dosage",
        validators=[DataRequired(message="Please enter dosage"), Length(max=100)],
    )
    scheduled_times = StringField(
        "Times (comma-separated)",
        validators=[DataRequired(message="Enter at least one time, e.g. 08:00, 12:00, 18:00")],
        description="e.g. 08:00, 12:00, 18:00",
    )
    instructions = StringField(
        "Instructions (optional)",
        validators=[Optional(), Length(max=500)],
    )
    start_date = DateField(
        "Start date (optional)",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    duration_days = IntegerField(
        "Duration in days (optional, use with start date)",
        validators=[Optional(), NumberRange(min=1)],
    )
    submit = SubmitField("Save")
