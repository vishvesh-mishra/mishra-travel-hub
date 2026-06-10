import os
import uuid
from datetime import datetime

from flask import flash, redirect, render_template, url_for
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Expense, ItineraryItem, JournalEntry, MemoryPhoto, Trip
from app.utils import memory_upload_dir

from . import bp
from .forms import DeleteJournalEntryForm, DeletePhotoForm, JournalEntryForm

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


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

    entries = (
        JournalEntry.query
        .options(selectinload(JournalEntry.photos))
        .filter_by(trip_id=trip.id)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())
        .all()
    )

    # Per-date expense totals — single grouped query, no N+1
    expense_rows = (
        db.session.query(Expense.expense_date, func.sum(Expense.amount))
        .filter(Expense.trip_id == trip.id)
        .group_by(Expense.expense_date)
        .all()
    )
    expenses_by_date = {d: total for d, total in expense_rows}

    # Per-date itinerary titles — single query, used for "related itinerary"
    itin_rows = (
        ItineraryItem.query
        .filter_by(trip_id=trip.id)
        .order_by(ItineraryItem.date.asc(), ItineraryItem.time.asc())
        .all()
    )
    itinerary_by_date = {}
    for item in itin_rows:
        itinerary_by_date.setdefault(item.date, []).append(item)

    return render_template(
        "journal/trip_journal.html",
        title="Memories",
        trip=trip,
        entries=entries,
        expenses_by_date=expenses_by_date,
        itinerary_by_date=itinerary_by_date,
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
            location=form.location.data.strip() if form.location.data else None,
        )
        db.session.add(entry)
        db.session.flush()  # get entry.id for photo rows
        _save_photos(form.photos.data, entry, trip)
        db.session.commit()
        flash("Memory saved.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    return render_template(
        "journal/form.html",
        title="New Memory",
        form=form,
        form_title="New Memory",
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
        entry.location = form.location.data.strip() if form.location.data else None
        _save_photos(form.photos.data, entry, trip)
        db.session.commit()
        flash("Memory updated.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    photo_delete_form = DeletePhotoForm()
    return render_template(
        "journal/form.html",
        title="Edit Memory",
        form=form,
        form_title="Edit Memory",
        trip=trip,
        entry=entry,
        photo_delete_form=photo_delete_form,
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
        _delete_photo_files(entry.photos)
        db.session.delete(entry)
        db.session.commit()
        flash("Memory deleted.", "success")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    return render_template(
        "journal/delete.html",
        title="Delete Memory",
        trip=trip,
        entry=entry,
        form=form,
    )


@bp.route("/trip/<int:trip_id>/<int:entry_id>/photo/<int:photo_id>/delete", methods=["POST"])
def delete_photo(trip_id, entry_id, photo_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    entry = journal_entry_for_trip(trip.id, entry_id)
    photo = MemoryPhoto.query.filter_by(id=photo_id, journal_entry_id=entry_id).first() if entry else None
    if entry is None or photo is None:
        flash("Photo not found.", "warning")
        return redirect(url_for("journal.for_trip", trip_id=trip.id))

    form = DeletePhotoForm()
    if form.validate_on_submit():
        _delete_photo_files([photo])
        db.session.delete(photo)
        db.session.commit()
        flash("Photo removed.", "success")
    return redirect(url_for("journal.edit", trip_id=trip.id, entry_id=entry.id))


# ---------------------------------------------------------------------------
# Photo helpers
# ---------------------------------------------------------------------------

def _save_photos(file_storages, entry, trip):
    """Save uploaded photos, extract EXIF dates, and suggest itinerary matches."""
    if not file_storages:
        return

    for fs in file_storages:
        if not fs or not fs.filename:
            continue
        ext = os.path.splitext(fs.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(memory_upload_dir(), filename)
        fs.save(filepath)

        taken_date = _exif_date(filepath)
        db.session.add(MemoryPhoto(
            journal_entry_id=entry.id,
            filename=filename,
            taken_date=taken_date,
        ))

        # EXIF suggestion — never auto-assign, only inform the user
        if taken_date and taken_date != entry.entry_date:
            match = (
                ItineraryItem.query
                .filter_by(trip_id=trip.id, date=taken_date)
                .order_by(ItineraryItem.time.asc())
                .first()
            )
            if match:
                flash(
                    f'Photo taken {taken_date.strftime("%b %-d, %Y")} — '
                    f'matches "{match.title}". Consider setting the memory date.',
                    "info",
                )


def _exif_date(filepath):
    """Return the EXIF DateTimeOriginal as a date, or None."""
    try:
        from PIL import Image
        from PIL.ExifTags import Base as ExifBase

        with Image.open(filepath) as img:
            exif = img.getexif()
            raw = (
                exif.get(ExifBase.DateTimeOriginal.value)
                or exif.get(ExifBase.DateTime.value)
            )
            if not raw:
                ifd = exif.get_ifd(0x8769)  # Exif IFD holds DateTimeOriginal
                raw = ifd.get(ExifBase.DateTimeOriginal.value) if ifd else None
            if raw:
                return datetime.strptime(str(raw)[:19], "%Y:%m:%d %H:%M:%S").date()
    except Exception:
        pass
    return None


def _delete_photo_files(photos):
    upload_dir = memory_upload_dir()
    for photo in photos:
        try:
            path = os.path.join(upload_dir, photo.filename)
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def journal_entry_for_trip(trip_id, entry_id):
    return JournalEntry.query.filter_by(id=entry_id, trip_id=trip_id).first()
