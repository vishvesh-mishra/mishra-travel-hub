from datetime import date, datetime
from types import SimpleNamespace

from flask import current_app, render_template, send_from_directory, url_for
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (
    Document,
    Expense,
    ItineraryItem,
    JournalEntry,
    ShoppingItem,
    TravelGuideEntry,
    Trip,
)
from app.utils import compute_readiness, memory_upload_dir

from . import bp

_COUNTRY_FLAGS = {
    "united states": "🇺🇸",
    "usa": "🇺🇸",
    "uk": "🇬🇧",
    "united kingdom": "🇬🇧",
    "england": "🇬🇧",
    "india": "🇮🇳",
    "france": "🇫🇷",
    "germany": "🇩🇪",
    "italy": "🇮🇹",
    "spain": "🇪🇸",
    "japan": "🇯🇵",
    "australia": "🇦🇺",
    "canada": "🇨🇦",
    "thailand": "🇹🇭",
    "singapore": "🇸🇬",
    "dubai": "🇦🇪",
    "uae": "🇦🇪",
    "switzerland": "🇨🇭",
    "brazil": "🇧🇷",
    "mexico": "🇲🇽",
    "new zealand": "🇳🇿",
}


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


@bp.route("/today")
def today_view():
    today = date.today()
    now_time = datetime.now().time()

    # Current trip: active first, else next upcoming
    current_trip = (
        Trip.query.filter(Trip.start_date <= today, Trip.end_date >= today)
        .order_by(Trip.start_date.asc())
        .first()
    )
    trip_state = "active" if current_trip else None
    if current_trip is None:
        current_trip = (
            Trip.query.filter(Trip.start_date > today)
            .order_by(Trip.start_date.asc())
            .first()
        )
        trip_state = "upcoming" if current_trip else None

    todays_items = []
    next_event = None
    next_event_minutes = None
    hotels = []
    transfers = []
    countdown_days = None

    if current_trip:
        countdown_days = (current_trip.start_date - today).days

        todays_items = (
            ItineraryItem.query
            .filter_by(trip_id=current_trip.id, date=today)
            .order_by(ItineraryItem.time.asc(), ItineraryItem.id.asc())
            .all()
        )

        # Next event: today with time still ahead, else next future item
        next_event = (
            ItineraryItem.query
            .filter(
                ItineraryItem.trip_id == current_trip.id,
                or_(
                    ItineraryItem.date > today,
                    and_(
                        ItineraryItem.date == today,
                        or_(ItineraryItem.time.is_(None), ItineraryItem.time >= now_time),
                    ),
                ),
            )
            .order_by(ItineraryItem.date.asc(), ItineraryItem.time.asc(), ItineraryItem.id.asc())
            .first()
        )
        if next_event and next_event.date == today and next_event.time:
            now_minutes = now_time.hour * 60 + now_time.minute
            ev_minutes = next_event.time.hour * 60 + next_event.time.minute
            next_event_minutes = max(0, ev_minutes - now_minutes)

        guide_rows = (
            TravelGuideEntry.query
            .filter(
                TravelGuideEntry.trip_id == current_trip.id,
                TravelGuideEntry.section.in_(["hotel", "transfer"]),
            )
            .order_by(TravelGuideEntry.sort_order, TravelGuideEntry.id)
            .all()
        )
        hotels    = [g for g in guide_rows if g.section == "hotel"]
        transfers = [g for g in guide_rows if g.section == "transfer"]

    return render_template(
        "main/today.html",
        title="Today",
        today=today,
        current_trip=current_trip,
        trip_state=trip_state,
        countdown_days=countdown_days,
        todays_items=todays_items,
        next_event=next_event,
        next_event_minutes=next_event_minutes,
        hotels=hotels,
        transfers=transfers,
        now_time=now_time,
    )


@bp.route("/wallet")
def wallet():
    documents = (
        Document.query
        .options(joinedload(Document.trip))
        .join(Trip)
        .order_by(Trip.start_date.desc(), Document.category.asc(), Document.id.asc())
        .all()
    )
    category_meta = {
        "Passport":     ("bi-person-badge",        "passport"),
        "Visa":         ("bi-patch-check",         "visa"),
        "Flight":       ("bi-airplane",            "flight"),
        "Hotel":        ("bi-building",            "hotel"),
        "Match Ticket": ("bi-ticket-perforated",   "ticket"),
        "Insurance":    ("bi-shield-check",        "insurance"),
        "Other":        ("bi-file-earmark",        "other"),
    }
    return render_template(
        "main/wallet.html",
        title="Travel Wallet",
        documents=documents,
        category_meta=category_meta,
    )


@bp.route("/media/memories/<path:filename>")
def memory_photo(filename):
    """Serve uploaded memory photos from the persistent upload directory.

    Uploads live outside the app tree (Render disk at /data) so they survive
    deploys; send_from_directory also guards against path traversal.
    """
    resp = send_from_directory(memory_upload_dir(), filename)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


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

    primary_trip_timeline = []
    primary_trip_expense_total = 0
    primary_trip_flag = "✈️"
    if primary_trip:
        primary_trip_timeline = (
            ItineraryItem.query
            .filter_by(trip_id=primary_trip.id)
            .order_by(ItineraryItem.date.asc(), ItineraryItem.time.asc())
            .all()
        )
        primary_trip_expense_total = (
            db.session.query(func.sum(Expense.amount))
            .filter(Expense.trip_id == primary_trip.id)
            .scalar()
        ) or 0
        dest = primary_trip.destination.lower()
        for kw, flag in _COUNTRY_FLAGS.items():
            if kw in dest:
                primary_trip_flag = flag
                break

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
        primary_trip_timeline=primary_trip_timeline,
        primary_trip_expense_total=primary_trip_expense_total,
        primary_trip_flag=primary_trip_flag,
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
