from flask import flash, redirect, render_template, url_for
from sqlalchemy import case, func

from app.extensions import db
from app.models import ShoppingItem, Trip

from . import bp
from .forms import DeleteShoppingItemForm, ShoppingItemForm, ToggleShoppingItemForm


@bp.route("/")
def index():
    total_count = func.count(ShoppingItem.id).label("total_count")
    completed_count = func.count(
        case((ShoppingItem.completed.is_(True), ShoppingItem.id))
    ).label("completed_count")
    trip_rows = (
        db.session.query(Trip, total_count, completed_count)
        .outerjoin(ShoppingItem)
        .group_by(Trip.id)
        .order_by(Trip.start_date.asc(), Trip.name.asc())
        .all()
    )
    sample_items = {}
    for trip, _total, _completed in trip_rows:
        sample_items[trip.id] = (
            ShoppingItem.query.filter_by(trip_id=trip.id)
            .order_by(ShoppingItem.completed.asc(), ShoppingItem.id.asc())
            .limit(4)
            .all()
        )
    return render_template("shopping/index.html", title="Shopping", trip_rows=trip_rows, sample_items=sample_items)


@bp.route("/trip/<int:trip_id>")
def for_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    items = shopping_items_query(trip.id).all()
    total_items, completed_items, progress_percentage = shopping_progress(trip.id)
    toggle_form = ToggleShoppingItemForm()
    return render_template(
        "shopping/trip_shopping.html",
        title="Shopping",
        trip=trip,
        items=items,
        total_items=total_items,
        completed_items=completed_items,
        progress_percentage=progress_percentage,
        toggle_form=toggle_form,
    )


@bp.route("/trip/<int:trip_id>/new", methods=["GET", "POST"])
def create(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = ShoppingItemForm()
    if form.validate_on_submit():
        item = ShoppingItem(
            trip_id=trip.id,
            item_name=form.item_name.data.strip(),
            category=form.category.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            completed=form.completed.data,
        )
        db.session.add(item)
        db.session.commit()
        flash("Shopping item created successfully.", "success")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    return render_template(
        "shopping/form.html",
        title="Add Shopping Item",
        form=form,
        form_title="Add Shopping Item",
        trip=trip,
    )


@bp.route("/trip/<int:trip_id>/<int:item_id>/edit", methods=["GET", "POST"])
def edit(trip_id, item_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    item = shopping_item_for_trip(trip.id, item_id)
    if item is None:
        flash("Shopping item not found.", "warning")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    form = ShoppingItemForm(obj=item)
    if form.validate_on_submit():
        item.item_name = form.item_name.data.strip()
        item.category = form.category.data
        item.notes = form.notes.data.strip() if form.notes.data else None
        item.completed = form.completed.data
        db.session.commit()
        flash("Shopping item updated successfully.", "success")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    return render_template(
        "shopping/form.html",
        title="Edit Shopping Item",
        form=form,
        form_title="Edit Shopping Item",
        trip=trip,
        item=item,
    )


@bp.route("/trip/<int:trip_id>/<int:item_id>/delete", methods=["GET", "POST"])
def delete(trip_id, item_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    item = shopping_item_for_trip(trip.id, item_id)
    if item is None:
        flash("Shopping item not found.", "warning")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    form = DeleteShoppingItemForm()
    if form.validate_on_submit():
        db.session.delete(item)
        db.session.commit()
        flash("Shopping item deleted successfully.", "success")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    return render_template(
        "shopping/delete.html",
        title="Delete Shopping Item",
        trip=trip,
        item=item,
        form=form,
    )


@bp.route("/trip/<int:trip_id>/<int:item_id>/toggle", methods=["POST"])
def toggle(trip_id, item_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    item = shopping_item_for_trip(trip.id, item_id)
    if item is None:
        flash("Shopping item not found.", "warning")
        return redirect(url_for("shopping.for_trip", trip_id=trip.id))

    form = ToggleShoppingItemForm()
    if form.validate_on_submit():
        item.completed = not item.completed
        db.session.commit()
        flash("Shopping item updated.", "success")
    else:
        flash("Unable to update shopping item.", "warning")

    return redirect(url_for("shopping.for_trip", trip_id=trip.id))


def shopping_items_query(trip_id):
    return ShoppingItem.query.filter_by(trip_id=trip_id).order_by(
        ShoppingItem.completed.asc(),
        ShoppingItem.category.asc(),
        ShoppingItem.item_name.asc(),
        ShoppingItem.id.asc(),
    )


def shopping_item_for_trip(trip_id, item_id):
    return ShoppingItem.query.filter_by(id=item_id, trip_id=trip_id).first()


def shopping_progress(trip_id):
    total_items = ShoppingItem.query.filter_by(trip_id=trip_id).count()
    completed_items = ShoppingItem.query.filter_by(trip_id=trip_id, completed=True).count()
    progress_percentage = round((completed_items / total_items) * 100) if total_items else 0
    return total_items, completed_items, progress_percentage
