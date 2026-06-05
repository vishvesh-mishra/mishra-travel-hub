from datetime import date, datetime
from types import SimpleNamespace

from flask import current_app, render_template, send_from_directory, url_for
from sqlalchemy import and_, case, func, or_

from app.extensions import db
from app.models import Document, Expense, ItineraryItem, JournalEntry, ShoppingItem, Trip
from app.utils import compute_readiness

from . import bp


@bp.route("/hub")
def hub():
    import os

    is_production = os.environ.get("FLASK_CONFIG") == "production"
    app_version = "1.0"
    deploy_platform = "Render" if is_production else "Local"

    db_size_str = "Active"
    try:
        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite" in db_url:
            if db_url.startswith("sqlite:////"):
                db_path = db_url[len("sqlite:///"):]
            elif db_url.startswith("sqlite:///"):
                db_path = os.path.join(os.getcwd(), db_url[len("sqlite:///"):])
            else:
                db_path = None
            if db_path and os.path.exists(db_path):
                size = os.path.getsize(db_path)
                db_size_str = f"{max(1, size // 1024)} KB"
    except Exception:
        pass

    return render_template(
        "main/hub.html",
        title="Hub",
        app_version=app_version,
        deploy_platform=deploy_platform,
        db_size=db_size_str,
        is_production=is_production,
    )


@bp.route("/sw.js")
def service_worker():
    resp = send_from_directory(current_app.static_folder, "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


@bp.route("/")
def dashboard():
    today = date.today()
    current_time = datetime.now().time()

    active_trips = normalize_trip_rows(trips_with_counts_query().filter(
        Trip.start_date <= today,
        Trip.end_date >= today,
    ).order_by(Trip.start_date.asc()).all())

    upcoming_trips = normalize_trip_rows(trips_with_counts_query().filter(
        Trip.start_date > today,
    ).order_by(Trip.start_date.asc()).all())

    next_trip_row = upcoming_trips[0] if upcoming_trips else None
    next_trip = next_trip_row.trip if next_trip_row else None
    next_trip_countdown = (next_trip.start_date - today).days if next_trip else None
    next_trip_shopping_total = next_trip_row.shopping_count if next_trip_row else 0
    next_trip_shopping_remaining = next_trip_row.shopping_remaining if next_trip_row else 0

    next_itinerary_item = (
        ItineraryItem.query.join(Trip)
        .filter(
            or_(
                ItineraryItem.date > today,
                and_(ItineraryItem.date == today, ItineraryItem.time >= current_time),
            )
        )
        .order_by(ItineraryItem.date.asc(), ItineraryItem.time.asc(), ItineraryItem.id.asc())
        .first()
    )

    fallback_trip = Trip.query.order_by(Trip.start_date.desc(), Trip.id.desc()).first()
    primary_trip = next_trip or (active_trips[0].trip if active_trips else fallback_trip)

    total_expense_spend = (
        db.session.query(func.sum(Expense.amount)).scalar()
    ) or 0
    total_expense_count = Expense.query.count()

    total_journal_count = JournalEntry.query.count()
    recent_journal_entry = (
        JournalEntry.query.join(Trip)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())
        .first()
    )

    all_dashboard_trips = active_trips + upcoming_trips
    readiness_map = {row.trip.id: compute_readiness(row.trip.id) for row in all_dashboard_trips}
    if primary_trip and primary_trip.id not in readiness_map:
        readiness_map[primary_trip.id] = compute_readiness(primary_trip.id)

    attention_alerts = []
    if primary_trip:
        r = readiness_map[primary_trip.id]
        pt_id = primary_trip.id
        if r["itinerary_count"] == 0:
            attention_alerts.append({
                "icon": "bi-map",
                "icon_color": "primary",
                "message": "No itinerary planned yet",
                "subtitle": "Add your trip plans and schedule",
                "action_url": url_for("trips.create_itinerary_item", trip_id=pt_id),
                "action_label": "Add",
            })
        if r["doc_count"] == 0:
            attention_alerts.append({
                "icon": "bi-file-earmark",
                "icon_color": "danger",
                "message": "No documents uploaded",
                "subtitle": "Add your passport and booking docs",
                "action_url": url_for("documents.create", trip_id=pt_id),
                "action_label": "Add",
            })
        if r["shopping_total"] > 0 and r["shopping_completed"] < r["shopping_total"]:
            remaining = r["shopping_total"] - r["shopping_completed"]
            pct = round((r["shopping_completed"] / r["shopping_total"]) * 100)
            attention_alerts.append({
                "icon": "bi-cart",
                "icon_color": "warning",
                "message": f'{remaining} shopping {"item" if remaining == 1 else "items"} remaining',
                "subtitle": f'{pct}% of your list is complete',
                "action_url": url_for("shopping.for_trip", trip_id=pt_id),
                "action_label": "View",
            })
        if r["expense_count"] == 0:
            attention_alerts.append({
                "icon": "bi-currency-dollar",
                "icon_color": "success",
                "message": "No expenses logged yet",
                "subtitle": "Track your trip expenses",
                "action_url": url_for("expenses.create", trip_id=pt_id),
                "action_label": "Add",
            })
        if r["journal_count"] == 0:
            attention_alerts.append({
                "icon": "bi-journal-text",
                "icon_color": "purple",
                "message": "No journal entries written",
                "subtitle": "Capture your memories",
                "action_url": url_for("journal.create", trip_id=pt_id),
                "action_label": "Add",
            })

    return render_template(
        "main/dashboard.html",
        title="Dashboard",
        active_trips=active_trips,
        upcoming_trips=upcoming_trips,
        next_trip=next_trip,
        next_trip_countdown=next_trip_countdown,
        next_trip_shopping_total=next_trip_shopping_total,
        next_trip_shopping_remaining=next_trip_shopping_remaining,
        next_itinerary_item=next_itinerary_item,
        primary_trip=primary_trip,
        total_expense_spend=total_expense_spend,
        total_expense_count=total_expense_count,
        total_journal_count=total_journal_count,
        recent_journal_entry=recent_journal_entry,
        readiness_map=readiness_map,
        attention_alerts=attention_alerts,
        today=today,
    )


def trips_with_counts_query():
    itinerary_count = func.count(func.distinct(ItineraryItem.id)).label("itinerary_count")
    document_count = func.count(func.distinct(Document.id)).label("document_count")
    shopping_count = func.count(func.distinct(ShoppingItem.id)).label("shopping_count")
    shopping_remaining = func.count(
        func.distinct(case((ShoppingItem.completed.is_(False), ShoppingItem.id)))
    ).label("shopping_remaining")
    status_order = case((Trip.start_date >= date.today(), 0), else_=1)

    return (
        db.session.query(
            Trip,
            itinerary_count,
            document_count,
            shopping_count,
            shopping_remaining,
        )
        .outerjoin(ItineraryItem, ItineraryItem.trip_id == Trip.id)
        .outerjoin(Document, Document.trip_id == Trip.id)
        .outerjoin(ShoppingItem, ShoppingItem.trip_id == Trip.id)
        .group_by(Trip.id)
        .order_by(status_order, Trip.start_date.asc(), Trip.end_date.asc())
    )


def normalize_trip_rows(rows):
    return [
        SimpleNamespace(
            trip=trip,
            itinerary_count=itinerary_count,
            document_count=document_count,
            shopping_count=shopping_count,
            shopping_remaining=shopping_remaining,
        )
        for trip, itinerary_count, document_count, shopping_count, shopping_remaining in rows
    ]
