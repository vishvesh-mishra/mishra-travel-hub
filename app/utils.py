from sqlalchemy import text

from app.extensions import db


def compute_readiness(trip_id):
    """Return trip readiness dict using a single correlated-subquery SQL call."""
    row = db.session.execute(
        text(
            "SELECT"
            " (SELECT COUNT(*) FROM document       WHERE trip_id = :t) AS doc_count,"
            " (SELECT COUNT(*) FROM shopping_item  WHERE trip_id = :t) AS shop_total,"
            " (SELECT COUNT(*) FROM shopping_item  WHERE trip_id = :t AND completed = 1) AS shop_done,"
            " (SELECT COUNT(*) FROM itinerary_item WHERE trip_id = :t) AS itin_count,"
            " (SELECT COUNT(*) FROM expense        WHERE trip_id = :t) AS exp_count,"
            " (SELECT COUNT(*) FROM journal_entry  WHERE trip_id = :t) AS jrn_count"
        ),
        {"t": trip_id},
    ).one()

    doc_count          = row.doc_count
    shopping_total     = row.shop_total
    shopping_completed = row.shop_done
    itinerary_count    = row.itin_count
    expense_count      = row.exp_count
    journal_count      = row.jrn_count

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
