#!/usr/bin/env python3
"""
seed_guide.py

Seeds the Travel Guide for the "USA 2026" trip.
Idempotent: existing records with the same title + section are skipped.

Usage (from project root):
    python seed_guide.py
"""

import sys

from app import create_app
from app.extensions import db
from app.models import TravelGuideEntry, Trip

TRIP_NAME = "USA 2026"

# (section, title, subtitle, detail1, detail2, detail3, body, maps_query, sort_order)
GUIDE_DATA = [

    # ---- Hotels ----
    (
        "hotel",
        "Holiday Inn NYC – Times Square",
        "350 West 40th Street, New York, NY 10018",
        "+1 (212) 581-8100",
        "Check-in: 11 Jun 2026",
        "Check-out: 17 Jun 2026",
        None,
        "Holiday Inn New York City Times Square",
        10,
    ),
    (
        "hotel",
        "Wingate by Wyndham Niagara Falls",
        "401 Buffalo Ave, Niagara Falls, NY 14303",
        "+1 (716) 285-5700",
        "Check-in: 17 Jun 2026",
        "Check-out: 19 Jun 2026",
        None,
        "Wingate by Wyndham Niagara Falls NY",
        20,
    ),

    # ---- Flights ----
    (
        "flight",
        "Outbound Flight to New York",
        "Mumbai (BOM) → New York JFK",
        "Check airline confirmation",
        "Arrival: 11 Jun 2026",
        "JFK International Airport",
        None,
        "John F. Kennedy International Airport",
        10,
    ),
    (
        "flight",
        "Return Flight from Buffalo",
        "Buffalo Niagara (BUF) → Mumbai (BOM)",
        "Check airline confirmation",
        "Departure: 19 Jun 2026",
        "Buffalo Niagara International Airport",
        None,
        "Buffalo Niagara International Airport",
        20,
    ),

    # ---- Transfers ----
    (
        "transfer",
        "Airport Arrival Transfer",
        "Private MPV",
        "JFK International Airport",
        "Holiday Inn Times Square, New York",
        "On arrival",
        None,
        "JFK Airport New York",
        10,
    ),
    (
        "transfer",
        "New York → Niagara Falls",
        "Coach Transfer",
        "Hotel Times Square, New York",
        "Wingate Niagara Falls",
        "17 Jun 2026 — depart morning",
        None,
        "Niagara Falls, NY",
        20,
    ),
    (
        "transfer",
        "Niagara Falls → Buffalo Airport",
        "Private MPV",
        "Wingate by Wyndham Niagara Falls",
        "Buffalo Niagara International Airport",
        "19 Jun 2026 — check departure time",
        None,
        "Buffalo Niagara International Airport",
        30,
    ),

    # ---- Booking IDs ----
    (
        "booking",
        "Holiday Inn Times Square",
        "See booking confirmation email",
        "See booking confirmation email",
        None, None,
        None,
        None,
        10,
    ),
    (
        "booking",
        "Wingate Niagara Falls",
        "See booking confirmation email",
        "See booking confirmation email",
        None, None,
        None,
        None,
        20,
    ),

    # ---- Emergency Contacts ----
    (
        "contact",
        "Tour Operator — Emergency Line",
        "Available 24 hours during the trip",
        "+91-XXXXXXXXXX",
        "WhatsApp available",
        None,
        None,
        None,
        10,
    ),
    (
        "contact",
        "US Emergency Services",
        "Police / Fire / Ambulance",
        "911",
        None, None,
        None,
        None,
        20,
    ),
    (
        "contact",
        "Indian Embassy — Washington DC",
        "2107 Massachusetts Ave NW, Washington DC",
        "+1 (202) 939-7000",
        "consular.washington@mea.gov.in",
        None,
        None,
        "Indian Embassy Washington DC",
        30,
    ),

    # ---- Travel Notes ----
    (
        "note",
        "Required Travel Documents",
        None, None, None, None,
        "Ensure all of the following are physically accessible:\n\n"
        "• Passport (valid at least 6 months beyond return date)\n"
        "• USA Visa\n"
        "• Flight Tickets (printed or digital)\n"
        "• Hotel confirmation print-outs\n"
        "• Travel Insurance certificate\n"
        "• PAN Card (for financial identification)\n"
        "• Emergency contact list",
        None,
        10,
    ),
    (
        "note",
        "Arrival Instructions — New York",
        None, None, None, None,
        "1. Clear US immigration — carry DS-160 and visa approval email.\n"
        "2. Collect checked baggage from carousel.\n"
        "3. Meet private transfer driver in Arrivals hall (name board).\n"
        "4. Journey to Holiday Inn Times Square — approx 45–60 min.\n"
        "5. Early check-in (before 3 PM) subject to availability.",
        None,
        20,
    ),
    (
        "note",
        "Niagara Falls Transfer Notes",
        None, None, None, None,
        "• Coach departs from hotel lobby — be ready 30 min early.\n"
        "• Journey approx 7–8 hours including rest stops.\n"
        "• Carry snacks and water for the journey.\n"
        "• Passports required at US–Canada border crossing if day trip to Canada is taken.",
        None,
        30,
    ),

    # ---- Do's & Don'ts ----
    (
        "rule",
        "New York City",
        None, None, None, None,
        "DO:\n"
        "• Use the subway — it's reliable and covers the whole city.\n"
        "• Book popular attractions in advance (SUMMIT, statue cruise).\n"
        "• Tip 18–20% at restaurants — it is expected.\n"
        "• Carry a portable charger for all-day outings.\n"
        "• Keep emergency cash (USD) separate from your wallet.\n\n"
        "DON'T:\n"
        "• Don't jaywalk — police do issue fines.\n"
        "• Don't leave bags unattended in public areas.\n"
        "• Don't exchange currency at airport kiosks — use ATMs.\n"
        "• Don't take unmarked taxis from the airport.",
        None,
        10,
    ),
    (
        "rule",
        "Niagara Falls",
        None, None, None, None,
        "DO:\n"
        "• Wear the provided ponchos for Maid of the Mist — you WILL get wet.\n"
        "• Book Cave of the Winds tickets in advance.\n"
        "• Carry valid ID — if crossing to Canada, a passport is required.\n"
        "• Wear comfortable, waterproof footwear.\n\n"
        "DON'T:\n"
        "• Don't lean over barriers at observation decks.\n"
        "• Don't leave valuables in the coach.",
        None,
        20,
    ),

    # ---- Travel Etiquette ----
    (
        "etiquette",
        "General USA Etiquette",
        None, None, None, None,
        "• Greet people with a smile — Americans are generally warm and friendly.\n"
        "• Queue politely — cutting lines is considered very rude.\n"
        "• Speak at a moderate volume in public; very loud conversations attract attention.\n"
        "• Tipping is a cultural norm: restaurants 18–20%, taxis 10–15%, hotel bellhop $2–5/bag.\n"
        "• Hold doors open for people behind you.\n"
        "• Say 'excuse me' when walking past someone or trying to get attention.\n"
        "• Public spaces (transport, restaurants) are non-smoking unless marked.\n"
        "• Photography of police officers or federal buildings may be restricted.",
        None,
        10,
    ),
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure table exists

        trip = Trip.query.filter_by(name=TRIP_NAME).first()
        if trip is None:
            print(f'Error: trip "{TRIP_NAME}" not found.')
            print("Create the trip in the app first, then re-run this script.")
            sys.exit(1)

        print(f'Seeding Travel Guide for: "{trip.name}" (id={trip.id})')

        created = skipped = 0
        for (section, title, subtitle, d1, d2, d3, body, maps_q, sort) in GUIDE_DATA:
            exists = TravelGuideEntry.query.filter_by(
                trip_id=trip.id, section=section, title=title
            ).first()
            if exists:
                skipped += 1
                continue
            db.session.add(TravelGuideEntry(
                trip_id=trip.id,
                section=section,
                title=title,
                subtitle=subtitle,
                detail1=d1,
                detail2=d2,
                detail3=d3,
                body=body,
                maps_query=maps_q,
                sort_order=sort,
            ))
            created += 1

        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            print(f"Error: {exc}")
            sys.exit(1)

        print(f"Created : {created}")
        print(f"Skipped : {skipped}")
        print("Done.")


if __name__ == "__main__":
    seed()
