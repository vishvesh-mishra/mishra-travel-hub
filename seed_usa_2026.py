#!/usr/bin/env python3
"""
seed_usa_2026.py

One-time seed script for the "USA 2026" trip.
Idempotent: safe to re-run; existing records are skipped, not duplicated.

Usage (from project root):
    python seed_usa_2026.py
"""

import sys
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Document, ItineraryItem, ShoppingItem, Trip

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

TRIP_NAME = "USA 2026"

# (date, title, description)
# time is left as None — ItineraryItem.time is nullable
ITINERARY = [
    (date(2026, 6, 11), "Arrival New York, Times Square", None),
    (date(2026, 6, 12), "Statue of Liberty Cruise, Hop On Hop Off Tour, SUMMIT One Vanderbilt", None),
    (date(2026, 6, 13), "FIFA Match Day / Leisure", None),
    (date(2026, 6, 14), "Washington DC Day Tour", None),
    (date(2026, 6, 15), "Boston Day Trip", None),
    (date(2026, 6, 16), "Philadelphia & Amish Village Day Trip", None),
    (date(2026, 6, 17), "Transfer New York to Niagara Falls", None),
    (date(2026, 6, 18), "Cave of the Winds, Maid of the Mist, Scenic Trolley", None),
    (date(2026, 6, 19), "Departure", None),
]

TRAVEL_NOTES = """\
Package Overview

--- Hotels ---

New York:
Holiday Inn New York City – Times Square
Check-in: 11 Jun 2026  →  Check-out: 17 Jun 2026

Niagara Falls:
Wingate by Wyndham Niagara Falls
Check-in: 17 Jun 2026  →  Check-out: 19 Jun 2026

--- Transfers ---

JFK Airport → Hotel
Private MPV

New York → Niagara Falls
Coach Transfer

Wingate Niagara → Buffalo Airport
Private MPV

--- Important Travel Notes ---

Required Documents:
- Passport
- Visa
- Flight Tickets
- PAN Card"""

# (title, category) — categories must match DOCUMENT_CATEGORIES in documents/forms.py:
# "Passport", "Visa", "Flight", "Hotel", "Match Ticket", "Insurance", "Other"
DOCUMENTS = [
    ("Passport", "Passport"),
    ("Visa", "Visa"),
    ("Flight Tickets", "Flight"),
    ("PAN Card", "Other"),
]

# (item_name, category) — categories must match SHOPPING_CATEGORIES in shopping/forms.py:
# "Clothing", "Electronics", "Souvenirs", "Gifts", "Food", "Other"
SHOPPING_ITEMS = [
    ("Universal Travel Adapter", "Other"),
    ("Power Bank", "Electronics"),
    ("Luggage Tags", "Other"),
    ("Travel Insurance Copy", "Other"),
    ("Prescription Medicines", "Other"),
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

def seed():
    app = create_app()
    with app.app_context():
        trip = Trip.query.filter_by(name=TRIP_NAME).first()
        if trip is None:
            print(f'Error: trip "{TRIP_NAME}" not found in the database.')
            print("Create the trip in the app first, then re-run this script.")
            sys.exit(1)

        print(f'Seeding trip: "{trip.name}" (id={trip.id})')
        print()

        # --- Itinerary items ---
        itin_created = itin_skipped = 0
        for item_date, title, description in ITINERARY:
            exists = ItineraryItem.query.filter_by(
                trip_id=trip.id,
                date=item_date,
                title=title,
            ).first()
            if exists:
                itin_skipped += 1
            else:
                db.session.add(ItineraryItem(
                    trip_id=trip.id,
                    date=item_date,
                    time=None,
                    title=title,
                    description=description,
                ))
                itin_created += 1

        # --- Travel notes (stored on Trip.notes) ---
        notes_created = notes_skipped = 0
        if trip.notes:
            notes_skipped = 1
        else:
            trip.notes = TRAVEL_NOTES
            notes_created = 1

        # --- Documents ---
        docs_created = docs_skipped = 0
        for title, category in DOCUMENTS:
            exists = Document.query.filter_by(
                trip_id=trip.id,
                title=title,
            ).first()
            if exists:
                docs_skipped += 1
            else:
                db.session.add(Document(
                    trip_id=trip.id,
                    title=title,
                    category=category,
                ))
                docs_created += 1

        # --- Shopping checklist ---
        shop_created = shop_skipped = 0
        for item_name, category in SHOPPING_ITEMS:
            exists = ShoppingItem.query.filter_by(
                trip_id=trip.id,
                item_name=item_name,
            ).first()
            if exists:
                shop_skipped += 1
            else:
                db.session.add(ShoppingItem(
                    trip_id=trip.id,
                    item_name=item_name,
                    category=category,
                    completed=False,
                ))
                shop_created += 1

        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            print(f"Error: database commit failed — {exc}")
            sys.exit(1)

        # --- Summary ---
        print(f"Created itinerary items : {itin_created}")
        print(f"Skipped itinerary items : {itin_skipped}")
        print()
        print(f"Created notes           : {notes_created}")
        print(f"Skipped notes           : {notes_skipped}")
        print()
        print(f"Created documents       : {docs_created}")
        print(f"Skipped documents       : {docs_skipped}")
        print()
        print(f"Created shopping items  : {shop_created}")
        print(f"Skipped shopping items  : {shop_skipped}")
        print()
        print("Done.")


if __name__ == "__main__":
    seed()
