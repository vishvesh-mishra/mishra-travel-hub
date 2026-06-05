from datetime import date

from flask import flash, redirect, render_template, url_for
from sqlalchemy import case, func

from app.extensions import db
from app.models import Document, Expense, ItineraryItem, ShoppingItem, Trip

from . import bp
from .forms import DeleteItineraryItemForm, DeleteTripForm, ItineraryItemForm, TripForm


@bp.route("/")
def index():
    today = date.today()
    trips = Trip.query.order_by(
        case((Trip.start_date >= today, 0), else_=1),
        Trip.start_date.asc(),
        Trip.end_date.asc(),
    ).all()
    return render_template("trips/index.html", title="Trips", trips=trips, today=today)


@bp.route("/new", methods=["GET", "POST"])
def create():
    form = TripForm()
    if form.validate_on_submit():
        trip = Trip(
            name=form.name.data.strip(),
            destination=form.destination.data.strip(),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            notes=form.notes.data.strip() if form.notes.data else None,
        )
        db.session.add(trip)
        db.session.commit()
        flash("Trip created successfully.", "success")
        return redirect(url_for("trips.detail", trip_id=trip.id))

    return render_template("trips/form.html", title="Create Trip", form=form, form_title="Create Trip")


@bp.route("/<int:trip_id>")
def detail(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    today = date.today()
    countdown_days = (trip.start_date - today).days
    duration_days = (trip.end_date - trip.start_date).days + 1
    upcoming_itinerary_items = itinerary_items_query(trip.id).filter(
        ItineraryItem.date >= today
    ).limit(5).all()
    next_itinerary_item = upcoming_itinerary_items[0] if upcoming_itinerary_items else None
    recent_documents = (
        Document.query.filter_by(trip_id=trip.id)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .limit(4)
        .all()
    )
    document_count = Document.query.filter_by(trip_id=trip.id).count()
    shopping_total = ShoppingItem.query.filter_by(trip_id=trip.id).count()
    shopping_completed = ShoppingItem.query.filter_by(
        trip_id=trip.id, completed=True
    ).count()
    shopping_progress = round((shopping_completed / shopping_total) * 100) if shopping_total else 0
    expense_total = (
        db.session.query(func.sum(Expense.amount))
        .filter(Expense.trip_id == trip.id)
        .scalar()
    ) or 0
    expense_count = Expense.query.filter_by(trip_id=trip.id).count()
    top_category_row = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.trip_id == trip.id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .first()
    )
    expense_top_category = top_category_row[0] if top_category_row else None
    return render_template(
        "trips/detail.html",
        title=trip.name,
        trip=trip,
        countdown_days=countdown_days,
        duration_days=duration_days,
        next_itinerary_item=next_itinerary_item,
        upcoming_itinerary_items=upcoming_itinerary_items,
        document_count=document_count,
        recent_documents=recent_documents,
        shopping_total=shopping_total,
        shopping_completed=shopping_completed,
        shopping_progress=shopping_progress,
        expense_total=expense_total,
        expense_count=expense_count,
        expense_top_category=expense_top_category,
        today=today,
    )


@bp.route("/<int:trip_id>/edit", methods=["GET", "POST"])
def edit(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = TripForm(obj=trip)
    if form.validate_on_submit():
        trip.name = form.name.data.strip()
        trip.destination = form.destination.data.strip()
        trip.start_date = form.start_date.data
        trip.end_date = form.end_date.data
        trip.notes = form.notes.data.strip() if form.notes.data else None
        db.session.commit()
        flash("Trip updated successfully.", "success")
        return redirect(url_for("trips.detail", trip_id=trip.id))

    return render_template(
        "trips/form.html",
        title="Edit Trip",
        form=form,
        form_title="Edit Trip",
        trip=trip,
    )


@bp.route("/<int:trip_id>/delete", methods=["GET", "POST"])
def delete(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = DeleteTripForm()
    if form.validate_on_submit():
        db.session.delete(trip)
        db.session.commit()
        flash("Trip deleted successfully.", "success")
        return redirect(url_for("trips.index"))

    return render_template("trips/delete.html", title="Delete Trip", trip=trip, form=form)


@bp.route("/<int:trip_id>/itinerary")
def itinerary(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    items = itinerary_items_query(trip.id).all()
    return render_template("trips/itinerary.html", title="Itinerary", trip=trip, items=items)


@bp.route("/<int:trip_id>/itinerary/new", methods=["GET", "POST"])
def create_itinerary_item(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = ItineraryItemForm(trip=trip)
    if form.validate_on_submit():
        item = ItineraryItem(
            trip_id=trip.id,
            date=form.date.data,
            time=form.time.data,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
        )
        db.session.add(item)
        db.session.commit()
        flash("Itinerary item created successfully.", "success")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))

    return render_template(
        "trips/itinerary_form.html",
        title="Add Itinerary Item",
        form=form,
        form_title="Add Itinerary Item",
        trip=trip,
    )


@bp.route("/<int:trip_id>/itinerary/<int:item_id>/edit", methods=["GET", "POST"])
def edit_itinerary_item(trip_id, item_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    item = itinerary_item_for_trip(trip.id, item_id)
    if item is None:
        flash("Itinerary item not found.", "warning")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))

    form = ItineraryItemForm(obj=item, trip=trip)
    if form.validate_on_submit():
        item.date = form.date.data
        item.time = form.time.data
        item.title = form.title.data.strip()
        item.description = form.description.data.strip() if form.description.data else None
        db.session.commit()
        flash("Itinerary item updated successfully.", "success")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))

    return render_template(
        "trips/itinerary_form.html",
        title="Edit Itinerary Item",
        form=form,
        form_title="Edit Itinerary Item",
        trip=trip,
        item=item,
    )


@bp.route("/<int:trip_id>/itinerary/<int:item_id>/delete", methods=["GET", "POST"])
def delete_itinerary_item(trip_id, item_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    item = itinerary_item_for_trip(trip.id, item_id)
    if item is None:
        flash("Itinerary item not found.", "warning")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))

    form = DeleteItineraryItemForm()
    if form.validate_on_submit():
        db.session.delete(item)
        db.session.commit()
        flash("Itinerary item deleted successfully.", "success")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))

    return render_template(
        "trips/itinerary_delete.html",
        title="Delete Itinerary Item",
        trip=trip,
        item=item,
        form=form,
    )


def itinerary_items_query(trip_id):
    return ItineraryItem.query.filter_by(trip_id=trip_id).order_by(
        ItineraryItem.date.asc(),
        ItineraryItem.time.asc(),
        ItineraryItem.id.asc(),
    )


def itinerary_item_for_trip(trip_id, item_id):
    return ItineraryItem.query.filter_by(id=item_id, trip_id=trip_id).first()
