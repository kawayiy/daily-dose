from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.forms.auth import LoginForm, RegisterForm
from app.services.user_service import UserService

auth_bp = Blueprint("auth", __name__)


# def _safe_next_url(default_endpoint: str = "main.index") -> str:
#     nxt = request.args.get("next")
#     if not nxt:
#         return url_for(default_endpoint)
#     parsed = urlparse(nxt)
#     if parsed.scheme or parsed.netloc:
#         return url_for(default_endpoint)
#     return nxt

def _post_login_redirect(user):
    if getattr(user, "role", None) == "carer":
        return redirect(url_for("carer.dependents_list"))
    return redirect(url_for("schedule.plan"))  

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = UserService.get_user_by_email(form.email.data)
        if not user or not UserService.verify_password(user, form.password.data):
            flash("Invalid email or password")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember.data)
        flash("Logged in")
        return _post_login_redirect(user)
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = UserService.register(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data,
                phone=form.phone.data,
                age=form.age.data,
            )
        except Exception as e:
            flash(str(e))
            return render_template("auth/register.html", form=form)

        login_user(user)
        flash("Registered")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out")
    return redirect(url_for("main.index"))