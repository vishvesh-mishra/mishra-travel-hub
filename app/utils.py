from app.extensions import db
from app.models import Document, Expense, ItineraryItem, JournalEntry, ShoppingItem


def compute_readiness(trip_id):
    doc_count = Document.query.filter_by(trip_id=trip_id).count()
    shopping_total = ShoppingItem.query.filter_by(trip_id=trip_id).count()
    shopping_completed = ShoppingItem.query.filter_by(trip_id=trip_id, completed=True).count()
    itinerary_count = ItineraryItem.query.filter_by(trip_id=trip_id).count()
    expense_count = Expense.query.filter_by(trip_id=trip_id).count()
    journal_count = JournalEntry.query.filter_by(trip_id=trip_id).count()

    score = 0
    score += 20 if doc_count > 0 else 0
    score += round((shopping_completed / shopping_total) * 20) if shopping_total > 0 else 0
    score += 20 if itinerary_count > 0 else 0
    score += 20 if expense_count > 0 else 0
    score += 20 if journal_count > 0 else 0

    if score >= 80:
        label, color = "Ready", "success"
    elif score >= 60:
        label, color = "Nearly Ready", "warning"
    elif score >= 20:
        label, color = "Planning", "info"
    else:
        label, color = "Just Started", "secondary"

    return {
        "score": score,
        "label": label,
        "color": color,
        "doc_count": doc_count,
        "shopping_total": shopping_total,
        "shopping_completed": shopping_completed,
        "itinerary_count": itinerary_count,
        "expense_count": expense_count,
        "journal_count": journal_count,
    }
