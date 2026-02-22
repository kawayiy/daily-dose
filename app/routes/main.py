
from flask import Blueprint, jsonify, redirect, url_for

from app.services.item_service import ItemService

from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    if getattr(current_user, "role", None) == "carer":
        return redirect(url_for("carer.dependents_list"))

    return redirect(url_for("schedule.plan"))


@main_bp.route("/demo-db")
def demo_db():
    
    ItemService.add_item("test-name")
    return jsonify(ItemService.get_all_items())

