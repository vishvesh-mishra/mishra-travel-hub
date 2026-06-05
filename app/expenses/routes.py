from flask import flash, redirect, render_template, url_for
from sqlalchemy import func

from app.extensions import db
from app.models import Expense, Trip

from . import bp
from .forms import DeleteExpenseForm, ExpenseForm


@bp.route("/")
def index():
    trip_rows = (
        db.session.query(
            Trip,
            func.count(Expense.id).label("expense_count"),
            func.sum(Expense.amount).label("total_spend"),
        )
        .outerjoin(Expense)
        .group_by(Trip.id)
        .order_by(Trip.start_date.asc(), Trip.name.asc())
        .all()
    )
    return render_template("expenses/index.html", title="Expenses", trip_rows=trip_rows)


@bp.route("/trip/<int:trip_id>")
def for_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    expenses = expenses_query(trip.id).all()
    total_spend, expense_count, category_totals = expense_summary(trip.id)
    return render_template(
        "expenses/trip_expenses.html",
        title="Expenses",
        trip=trip,
        expenses=expenses,
        total_spend=total_spend,
        expense_count=expense_count,
        category_totals=category_totals,
    )


@bp.route("/trip/<int:trip_id>/new", methods=["GET", "POST"])
def create(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    form = ExpenseForm(trip=trip)
    if form.validate_on_submit():
        expense = Expense(
            trip_id=trip.id,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data.strip() if form.description.data else None,
            expense_date=form.expense_date.data,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses.for_trip", trip_id=trip.id))

    return render_template(
        "expenses/form.html",
        title="Add Expense",
        form=form,
        form_title="Add Expense",
        trip=trip,
    )


@bp.route("/trip/<int:trip_id>/<int:expense_id>/edit", methods=["GET", "POST"])
def edit(trip_id, expense_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    expense = expense_for_trip(trip.id, expense_id)
    if expense is None:
        flash("Expense not found.", "warning")
        return redirect(url_for("expenses.for_trip", trip_id=trip.id))

    form = ExpenseForm(obj=expense, trip=trip)
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.description = form.description.data.strip() if form.description.data else None
        expense.expense_date = form.expense_date.data
        db.session.commit()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expenses.for_trip", trip_id=trip.id))

    return render_template(
        "expenses/form.html",
        title="Edit Expense",
        form=form,
        form_title="Edit Expense",
        trip=trip,
        expense=expense,
    )


@bp.route("/trip/<int:trip_id>/<int:expense_id>/delete", methods=["GET", "POST"])
def delete(trip_id, expense_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        flash("Trip not found.", "warning")
        return redirect(url_for("trips.index"))

    expense = expense_for_trip(trip.id, expense_id)
    if expense is None:
        flash("Expense not found.", "warning")
        return redirect(url_for("expenses.for_trip", trip_id=trip.id))

    form = DeleteExpenseForm()
    if form.validate_on_submit():
        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully.", "success")
        return redirect(url_for("expenses.for_trip", trip_id=trip.id))

    return render_template(
        "expenses/delete.html",
        title="Delete Expense",
        trip=trip,
        expense=expense,
        form=form,
    )


def expenses_query(trip_id):
    return Expense.query.filter_by(trip_id=trip_id).order_by(
        Expense.expense_date.desc(),
        Expense.id.desc(),
    )


def expense_for_trip(trip_id, expense_id):
    return Expense.query.filter_by(id=expense_id, trip_id=trip_id).first()


def expense_summary(trip_id):
    total_spend = (
        db.session.query(func.sum(Expense.amount))
        .filter(Expense.trip_id == trip_id)
        .scalar()
    ) or 0
    expense_count = Expense.query.filter_by(trip_id=trip_id).count()
    category_rows = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.trip_id == trip_id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    return total_spend, expense_count, list(category_rows)
