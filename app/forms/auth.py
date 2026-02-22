from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

from app.models.users import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])

    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=72)])
    password_confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )

    role = SelectField(
        "Role",
        choices=[
            (User.ROLE_DEPENDENT, "Dependent (被照护人)"),
            (User.ROLE_CARER, "Carer (照护者)"),
        ],
        validators=[DataRequired()],
    )

    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=20)])
    age = IntegerField("Age (optional)", validators=[Optional(), NumberRange(min=1, max=120)])

    submit = SubmitField("Register")