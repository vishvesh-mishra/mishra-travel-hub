# Mishra Travel Hub

A private Flask travel management portal for Vishvesh and family.

This repository currently contains the foundational architecture only:

- Flask application factory
- SQLAlchemy configuration
- Flask-Login configuration
- Core database models
- Feature blueprints
- Bootstrap 5 base template

CRUD workflows, forms, file uploads, and authentication behavior will be added in later iterations.

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
flask --app app.py run --debug
```

Open the local site:

```text
http://127.0.0.1:5000
```

## Configuration

The app reads configuration from `config.py`.

Useful environment variables:

- `SECRET_KEY`: Flask secret key. Required for production.
- `DATABASE_URL`: Database connection string. Defaults to SQLite at `instance/mishra_travel_hub.sqlite`.
- `FLASK_CONFIG`: `development` or `production`. Defaults to `development`.

## Database

The SQLAlchemy models are defined in `app/models.py`. To create tables locally from the Flask shell:

```bash
flask --app app.py shell
```

Then run:

```python
from app.extensions import db
db.create_all()
```
