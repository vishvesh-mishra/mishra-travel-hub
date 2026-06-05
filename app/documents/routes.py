from flask import flash, redirect, render_template, url_for
from sqlalchemy import case, func

from app.extensions import db
from app.models import Document, Trip

from . import bp
from .forms import DeleteDocumentForm, DocumentForm


@bp.route("/")
def index():
    trip_rows = (
        db.session.query(Trip, func.count(Document.id))
        .outerjoin(Document)
        .group_by(Trip.id)
        .order_by(Trip.start_date.asc(), Trip.name.asc())
        .all()
    )
    recent_documents = (
        Document.query.join(Trip)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .limit(6)
        .all()
    )
    return render_template(
        "documents/index.html",
        title="Documents",
        trip_rows=trip_rows,
        recent_documents=recent_documents,
    )


@bp.route("/trip/<int:trip_id>")
def for_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    documents = documents_query(trip.id).all()
    return render_template(
        "documents/trip_documents.html",
        title="Documents",
        trip=trip,
        documents=documents,
    )


@bp.route("/trip/<int:trip_id>/new", methods=["GET", "POST"])
def create(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = DocumentForm()
    if form.validate_on_submit():
        document = Document(
            trip_id=trip.id,
            title=form.title.data.strip(),
            category=form.category.data,
            external_url=form.external_url.data.strip() if form.external_url.data else None,
            notes=form.notes.data.strip() if form.notes.data else None,
        )
        db.session.add(document)
        db.session.commit()
        flash("Document created successfully.", "success")
        return redirect(url_for("documents.for_trip", trip_id=trip.id))

    return render_template(
        "documents/form.html",
        title="Add Document",
        form=form,
        form_title="Add Document",
        trip=trip,
    )


@bp.route("/trip/<int:trip_id>/<int:document_id>/edit", methods=["GET", "POST"])
def edit(trip_id, document_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    document = document_for_trip(trip.id, document_id)
    if document is None:
        flash("Document not found.", "warning")
        return redirect(url_for("documents.for_trip", trip_id=trip.id))

    form = DocumentForm(obj=document)
    if form.validate_on_submit():
        document.title = form.title.data.strip()
        document.category = form.category.data
        document.external_url = form.external_url.data.strip() if form.external_url.data else None
        document.notes = form.notes.data.strip() if form.notes.data else None
        db.session.commit()
        flash("Document updated successfully.", "success")
        return redirect(url_for("documents.for_trip", trip_id=trip.id))

    return render_template(
        "documents/form.html",
        title="Edit Document",
        form=form,
        form_title="Edit Document",
        trip=trip,
        document=document,
    )


@bp.route("/trip/<int:trip_id>/<int:document_id>/delete", methods=["GET", "POST"])
def delete(trip_id, document_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    document = document_for_trip(trip.id, document_id)
    if document is None:
        flash("Document not found.", "warning")
        return redirect(url_for("documents.for_trip", trip_id=trip.id))

    form = DeleteDocumentForm()
    if form.validate_on_submit():
        db.session.delete(document)
        db.session.commit()
        flash("Document deleted successfully.", "success")
        return redirect(url_for("documents.for_trip", trip_id=trip.id))

    return render_template(
        "documents/delete.html",
        title="Delete Document",
        trip=trip,
        document=document,
        form=form,
    )


def documents_query(trip_id):
    category_order = case(
        (Document.category == "Passport", 0),
        (Document.category == "Visa", 1),
        (Document.category == "Flight", 2),
        (Document.category == "Hotel", 3),
        (Document.category == "Match Ticket", 4),
        (Document.category == "Insurance", 5),
        else_=6,
    )
    return Document.query.filter_by(trip_id=trip_id).order_by(
        category_order,
        Document.created_at.desc(),
        Document.id.desc(),
    )


def document_for_trip(trip_id, document_id):
    return Document.query.filter_by(id=document_id, trip_id=trip_id).first()
