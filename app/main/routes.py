from datetime import date, datetime
from types import SimpleNamespace

from flask import render_template
from sqlalchemy import and_, case, func, or_

from app.extensions import db
from app.models import Document, Expense, ItineraryItem, ShoppingItem, Trip

from . import bp


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
