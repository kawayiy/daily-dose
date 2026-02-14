# Daily Dose

A Flask-based web project, currently in early development.

## Tech Stack

- **Flask** — Web framework
- **Flask-SQLAlchemy** — ORM with SQLite (default: `instance/app.db`)
- **Flask-WTF / WTForms** — Forms
- **pytest** — Unit testing

## Project Structure

```
app/
├── config.py          # Config (SECRET_KEY, database URI)
├── __init__.py        # App init, route/model registration, table creation
├── models/            # Data models
│   ├── demo.py        # Item model (id, name)
│   └── users.py       # User-related (TODO)
├── routes/            # Routes
│   ├── main.py        # Home page, /demo-db demo endpoint
│   └── auth.py        # /login (TODO)
└── services/          # Business logic
    └── item_service.py  # Item CRUD, etc.
tests/                 # Tests (e.g. test_item_service, test_main)
```

## Current Features

- **`/`** — Home page; renders `index.html`
- **`/demo-db`** — Demo: adds an Item named "test-name" and returns all Items as JSON
- **`/login`** — Login route registered; logic not implemented yet

## Run & Test

- Install dependencies: `pip install -r requirements.txt`
- Run the app: from project root, `flask run` (set `FLASK_APP=app` or equivalent)
- Run tests: `pytest`

The database file is created on first use (`instance/app.db`); tables are created at startup via `db.create_all()`.
