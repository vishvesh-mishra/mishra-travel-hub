# Mishra Travel Hub

## Purpose

A private travel management portal for Vishvesh and family.

The application should be mobile-first and optimized for iPhone Safari.

The first trip will be USA 2026, but the platform must support unlimited future trips.

---

## Core Features

### Authentication

- Single shared family login
- Secure password authentication

### Trips

Users can:

- Create trip
- Edit trip
- Archive trip
- View trip dashboard

Each trip contains:

- Name
- Destination
- Start Date
- End Date
- Notes

---

### Itinerary

Each trip should support:

- Day-wise itinerary
- Time slots
- Notes
- Activities

---

### Documents

Store references to:

- Passport copies
- Visa
- Flights
- Hotels
- Match tickets
- Insurance

Documents may be:

- Uploaded
- Or linked to Google Drive

---

### Shopping Lists

Users can:

- Create checklist
- Mark items completed
- Categorize items

---

### Expense Tracker

Users can:

- Add expense
- Categorize expense
- View total spend

Categories:

- Food
- Travel
- Shopping
- Entertainment
- Miscellaneous

---

### Travel Journal

Users can:

- Add journal entry
- Add photos
- Add date

---

### Dashboard

Display:

- Upcoming trips
- Active trip
- Countdown
- Recent journal entries
- Shopping progress

---

## Technical Requirements

Backend:
- Flask
- SQLAlchemy
- SQLite

Frontend:
- Bootstrap 5

Deployment:
- Render

Design:
- Apple-inspired
- Mobile-first
- Dark mode

Future Expansion:
- Multi-user accounts
- Maps
- Recommendations
- AI travel assistant

## Version 1 Scope

The first release should prioritize simplicity and reliability.

Required pages:

- Login
- Dashboard
- Trips
- Trip Detail
- Itinerary
- Documents
- Shopping Lists
- Expenses
- Journal

Authentication:

- Single shared account
- No registration page
- Admin user created manually

Database Models:

Trip
- id
- name
- destination
- start_date
- end_date
- notes
- created_at

ItineraryItem
- id
- trip_id
- date
- time
- title
- description

Document
- id
- trip_id
- title
- document_type
- file_path
- external_url

ShoppingItem
- id
- trip_id
- item_name
- category
- completed

Expense
- id
- trip_id
- amount
- category
- description
- expense_date

JournalEntry
- id
- trip_id
- title
- content
- entry_date

UI Requirements:

- Responsive design
- Works well on iPhone Safari
- Dark mode support
- Apple-inspired clean interface

Non-Goals:

- Multi-user support
- Real-time collaboration
- Notifications
- Maps integration
- AI features

These may be added later.