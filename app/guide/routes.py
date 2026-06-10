from flask import flash, redirect, render_template, url_for

from app.extensions import db
from app.models import TravelGuideEntry, Trip

from . import bp
from .forms import DeleteGuideEntryForm, GuideEntryForm


@bp.route("/trip/<int:trip_id>")
def for_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entries = (
        TravelGuideEntry.query
        .filter_by(trip_id=trip_id)
        .order_by(TravelGuideEntry.sort_order, TravelGuideEntry.id)
        .all()
    )

    # Group by section in canonical display order
    sections = {}
    for key in TravelGuideEntry.SECTION_ORDER:
        group = [e for e in entries if e.section == key]
        if group:
            sections[key] = group

    return render_template(
        "travel_guide/index.html",
        title="Travel Guide",
        trip=trip,
        sections=sections,
        section_meta=TravelGuideEntry.SECTION_META,
        has_entries=bool(entries),
    )


@bp.route("/trip/<int:trip_id>/new", methods=["GET", "POST"])
def create(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = GuideEntryForm()
    if form.validate_on_submit():
        try:
            sort_order = int(form.sort_order.data) if form.sort_order.data else 0
        except ValueError:
            sort_order = 0

        entry = TravelGuideEntry(
            trip_id=trip.id,
            section=form.section.data,
            title=form.title.data.strip(),
            subtitle=form.subtitle.data.strip() if form.subtitle.data else None,
            detail1=form.detail1.data.strip() if form.detail1.data else None,
            detail2=form.detail2.data.strip() if form.detail2.data else None,
            detail3=form.detail3.data.strip() if form.detail3.data else None,
            body=form.body.data.strip() if form.body.data else None,
            maps_query=form.maps_query.data.strip() if form.maps_query.data else None,
            sort_order=sort_order,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Guide entry added.", "success")
        return redirect(url_for("guide.for_trip", trip_id=trip.id))

    return render_template(
        "travel_guide/form.html",
        title="Add Guide Entry",
        form=form,
        form_title="Add Guide Entry",
        trip=trip,
    )


@bp.route("/trip/<int:trip_id>/<int:entry_id>/edit", methods=["GET", "POST"])
def edit(trip_id, entry_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entry = _entry_for_trip(trip.id, entry_id)
    if entry is None:
        flash("Guide entry not found.", "warning")
        return redirect(url_for("guide.for_trip", trip_id=trip.id))

    form = GuideEntryForm(obj=entry)
    if form.validate_on_submit():
        try:
            sort_order = int(form.sort_order.data) if form.sort_order.data else 0
        except ValueError:
            sort_order = 0

        entry.section    = form.section.data
        entry.title      = form.title.data.strip()
        entry.subtitle   = form.subtitle.data.strip() if form.subtitle.data else None
        entry.detail1    = form.detail1.data.strip() if form.detail1.data else None
        entry.detail2    = form.detail2.data.strip() if form.detail2.data else None
        entry.detail3    = form.detail3.data.strip() if form.detail3.data else None
        entry.body       = form.body.data.strip() if form.body.data else None
        entry.maps_query = form.maps_query.data.strip() if form.maps_query.data else None
        entry.sort_order = sort_order
        db.session.commit()
        flash("Guide entry updated.", "success")
        return redirect(url_for("guide.for_trip", trip_id=trip.id))

    return render_template(
        "travel_guide/form.html",
        title="Edit Guide Entry",
        form=form,
        form_title="Edit Guide Entry",
        trip=trip,
        entry=entry,
    )


@bp.route("/trip/<int:trip_id>/<int:entry_id>/delete", methods=["GET", "POST"])
def delete(trip_id, entry_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entry = _entry_for_trip(trip.id, entry_id)
    if entry is None:
        flash("Guide entry not found.", "warning")
        return redirect(url_for("guide.for_trip", trip_id=trip.id))

    form = DeleteGuideEntryForm()
    if form.validate_on_submit():
        db.session.delete(entry)
        db.session.commit()
        flash("Guide entry deleted.", "success")
        return redirect(url_for("guide.for_trip", trip_id=trip.id))

    return render_template(
        "travel_guide/delete.html",
        title="Delete Guide Entry",
        trip=trip,
        entry=entry,
        form=form,
    )


def _entry_for_trip(trip_id, entry_id):
    return TravelGuideEntry.query.filter_by(id=entry_id, trip_id=trip_id).first()
