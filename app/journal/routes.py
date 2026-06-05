from flask import flash, redirect, render_template, url_for
from sqlalchemy import func

from app.extensions import db
from app.models import JournalEntry, Trip

from . import bp
from .forms import DeleteJournalEntryForm, JournalEntryForm


@bp.route("/")
def index():
    trip_rows = (
        db.session.query(Trip, func.count(JournalEntry.id))
        .outerjoin(JournalEntry)
        .group_by(Trip.id)
        .order_by(Trip.start_date.asc(), Trip.name.asc())
        .all()
    )
    return render_template("journal/index.html", title="Journal", trip_rows=trip_rows)


@bp.route("/trip/<int:trip_id>")
def for_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entries = journal_entries_query(trip.id).all()
    return render_template(
        "journal/trip_journal.html",
        title="Journal",
        trip=trip,
        entries=entries,
    )


@bp.route("/trip/<int:trip_id>/new", methods=["GET", "POST"])
def create(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = JournalEntryForm(trip=trip)
    if form.validate_on_submit():
        entry = JournalEntry(
            trip_id=trip.id,
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            entry_date=form.entry_date.data,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry added successfully.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    return render_template(
        "journal/form.html",
        title="Add Journal Entry",
        form=form,
        form_title="Add Journal Entry",
        trip=trip,
    )


@bp.route("/trip/<int:trip_id>/<int:entry_id>/edit", methods=["GET", "POST"])
def edit(trip_id, entry_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entry = journal_entry_for_trip(trip.id, entry_id)
    if entry is None:
        flash("Journal entry not found.", "warning")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    form = JournalEntryForm(obj=entry, trip=trip)
    if form.validate_on_submit():
        entry.title = form.title.data.strip()
        entry.content = form.content.data.strip()
        entry.entry_date = form.entry_date.data
        db.session.commit()
        flash("Journal entry updated successfully.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    return render_template(
        "journal/form.html",
        title="Edit Journal Entry",
        form=form,
        form_title="Edit Journal Entry",
        trip=trip,
        entry=entry,
    )


@bp.route("/trip/<int:trip_id>/<int:entry_id>/delete", methods=["GET", "POST"])
def delete(trip_id, entry_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entry = journal_entry_for_trip(trip.id, entry_id)
    if entry is None:
        flash("Journal entry not found.", "warning")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    form = DeleteJournalEntryForm()
    if form.validate_on_submit():
        db.session.delete(entry)
        db.session.commit()
        flash("Journal entry deleted successfully.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    return render_template(
        "journal/delete.html",
        title="Delete Journal Entry",
        trip=trip,
        entry=entry,
        form=form,
    )


def journal_entries_query(trip_id):
    return JournalEntry.query.filter_by(trip_id=trip_id).order_by(
        JournalEntry.entry_date.desc(),
        JournalEntry.id.desc(),
    )


def journal_entry_for_trip(trip_id, entry_id):
    return JournalEntry.query.filter_by(id=entry_id, trip_id=trip_id).first()
