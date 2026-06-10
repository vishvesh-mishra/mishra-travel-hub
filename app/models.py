from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(160), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    itinerary_items = db.relationship(
        "ItineraryItem", back_populates="trip", cascade="all, delete-orphan"
    )
    documents = db.relationship(
        "Document", back_populates="trip", cascade="all, delete-orphan"
    )
    shopping_items = db.relationship(
        "ShoppingItem", back_populates="trip", cascade="all, delete-orphan"
    )
    expenses = db.relationship(
        "Expense", back_populates="trip", cascade="all, delete-orphan"
    )
    journal_entries = db.relationship(
        "JournalEntry", back_populates="trip", cascade="all, delete-orphan"
    )
    guide_entries = db.relationship(
        "TravelGuideEntry", back_populates="trip", cascade="all, delete-orphan"
    )


class ItineraryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)

    trip = db.relationship("Trip", back_populates="itinerary_items")


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    external_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    trip = db.relationship("Trip", back_populates="documents")


class ShoppingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    item_name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    trip = db.relationship("Trip", back_populates="shopping_items")


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    expense_date = db.Column(db.Date, nullable=False)

    trip = db.relationship("Trip", back_populates="expenses")


class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    content = db.Column(db.Text)
    entry_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))

    trip = db.relationship("Trip", back_populates="journal_entries")
    photos = db.relationship(
        "MemoryPhoto", back_populates="entry", cascade="all, delete-orphan",
        order_by="MemoryPhoto.id",
    )


class MemoryPhoto(db.Model):
    __tablename__ = "memory_photo"

    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(
        db.Integer, db.ForeignKey("journal_entry.id"), nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)  # relative to static/uploads/memories/
    taken_date = db.Column(db.Date)                       # from EXIF when available
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    entry = db.relationship("JournalEntry", back_populates="photos")


class TravelGuideEntry(db.Model):
    __tablename__ = "travel_guide_entry"

    # section → (bootstrap-icon class, display label)
    SECTION_META = {
        "hotel":     ("bi-building",            "Hotels"),
        "flight":    ("bi-airplane",             "Flights"),
        "transfer":  ("bi-bus-front",            "Transfers"),
        "booking":   ("bi-ticket-perforated",    "Booking IDs"),
        "contact":   ("bi-telephone",            "Emergency Contacts"),
        "note":      ("bi-info-circle",          "Travel Notes"),
        "rule":      ("bi-check2-square",        "Do's & Don'ts"),
        "etiquette": ("bi-heart",                "Travel Etiquette"),
    }
    SECTION_ORDER = ["hotel", "flight", "transfer", "booking", "contact", "note", "rule", "etiquette"]

    id         = db.Column(db.Integer, primary_key=True)
    trip_id    = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    section    = db.Column(db.String(40), nullable=False)   # one of SECTION_META keys
    title      = db.Column(db.String(160), nullable=False)
    subtitle   = db.Column(db.String(200))   # address / route / phone org
    detail1    = db.Column(db.String(200))   # phone / departure / pickup / ref number
    detail2    = db.Column(db.String(200))   # check-in / arrival / drop
    detail3    = db.Column(db.String(200))   # check-out / terminal / reporting time
    body       = db.Column(db.Text)          # free text for notes/rules/etiquette
    maps_query = db.Column(db.String(300))   # passed to Google Maps search URL
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    trip = db.relationship("Trip", back_populates="guide_entries")
