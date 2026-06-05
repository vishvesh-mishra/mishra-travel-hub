# Mishra Travel Hub

A private Flask travel management portal for Vishvesh and family.

## Features

- Trips — create, edit, view, delete
- Itinerary — day-wise schedule per trip
- Documents — Google Drive links organized by trip
- Shopping — packing checklists with progress tracking
- Expenses — spend tracking with category breakdown
- Journal — travel diary entries per trip
- Dashboard — countdown, itinerary, expense, and journal summary
- Authentication — single shared family account

## Local Setup

### Prerequisites

- Python 3.11 or later

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Initialize the database

```bash
flask --app app init-db
```

### Create the admin user

```bash
flask --app app create-admin
```

You will be prompted for a username and password.

### Run

```bash
flask --app app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) and sign in.

---

## Deployment on Render

### One-click deploy

The repository includes a `render.yaml` that configures everything automatically.

1. Push this repository to GitHub.
2. In the [Render dashboard](https://dashboard.render.com), click **New → Blueprint**.
3. Connect your GitHub repository.
4. Render will detect `render.yaml` and provision the service with a persistent disk and an auto-generated `SECRET_KEY`.
5. After the first deploy completes, open a **Shell** tab in your Render service and run:

```bash
flask --app app create-admin
```

6. Log in at your Render URL.

### What render.yaml provisions

| Resource | Detail |
|---|---|
| Web service | Python, 2 Gunicorn workers |
| Persistent disk | 1 GB mounted at `/data` — SQLite stored here |
| `SECRET_KEY` | Auto-generated on first deploy |
| `DATABASE_URL` | `sqlite:////data/mishra_travel_hub.sqlite` |
| `FLASK_CONFIG` | `production` |

### Manual deploy (without render.yaml)

1. Create a **Web Service** on Render pointing to your repository.
2. Set **Build Command**: `pip install -r requirements.txt`
3. Set **Start Command**: `flask --app app init-db && gunicorn wsgi:app`
4. Add a **Persistent Disk** mounted at `/data`.
5. Set environment variables:

| Variable | Value |
|---|---|
| `FLASK_CONFIG` | `production` |
| `SECRET_KEY` | A long random string (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | `sqlite:////data/mishra_travel_hub.sqlite` |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes in production | `dev-change-me` | Flask session signing key — never use the default in production |
| `DATABASE_URL` | No | `sqlite:///instance/mishra_travel_hub.sqlite` | SQLAlchemy connection string |
| `FLASK_CONFIG` | No | `development` | `development` or `production` |

---

## Deployment Checklist

- [ ] `SECRET_KEY` is set to a strong random value (not `dev-change-me`)
- [ ] `FLASK_CONFIG=production` is set
- [ ] `DATABASE_URL` points to a path on the persistent disk
- [ ] Admin user created with `flask --app app create-admin`
- [ ] HTTPS is enforced (Render provides TLS automatically)
- [ ] Application loads without errors in the Render logs

---

## Local CLI Commands

```bash
# Create database tables
flask --app app init-db

# Create the admin user
flask --app app create-admin
```
