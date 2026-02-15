
from flask import Blueprint, render_template, jsonify

from app.services.item_service import ItemService

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/demo-db")
def demo_db():
    
    ItemService.add_item("test-name")
    return jsonify(ItemService.get_all_items())

