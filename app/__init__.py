from flask import Flask

from app.config import CurrentConfig
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(CurrentConfig)

db = SQLAlchemy(app)

from app.models import demo

# from app.routes import auth, main
from app.routes.main import main_bp
from app.routes.auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

'''
1. Ensure we run inside the Flask application context so db has access to app config.
2. create_all() creates the DB file (e.g. instance/app.db) if missing and all 
tables from models.
'''
with app.app_context():
    db.create_all()




