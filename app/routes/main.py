from app import app
from flask import render_template, jsonify

from app.services.item_service import ItemService


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/demo-db")
def demo_db():
    
    ItemService.add_item("test-name")
    return jsonify(ItemService.get_all_items())

