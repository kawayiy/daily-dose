from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from app.config import CurrentConfig
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(CurrentConfig)

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
from app.models import schedule  # noqa: F401 - register Schedule, Prescription, Medication

@login_manager.user_loader
def load_user(user_id: str):
    from app.models.users import User
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

# from app.routes import auth, main
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.schedule import schedule_bp
from app.routes.carer import carer_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(carer_bp)

'''
1. Ensure we run inside the Flask application context so db has access to app config.
2. create_all() creates the DB file (e.g. instance/app.db) if missing and all 
tables from models.
'''
with app.app_context():
    db.create_all()




