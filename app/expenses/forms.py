from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


EXPENSE_CATEGORIES = [
    ("Food", "Food"),
    ("Travel", "Travel"),
    ("Shopping", "Shopping"),
    ("Entertainment", "Entertainment"),
    ("Accommodation", "Accommodation"),
    ("Miscellaneous", "Miscellaneous"),
]


class ExpenseForm(FlaskForm):
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[DataRequired(message="Amount is required.")],
    )
    category = SelectField(
        "Category",
        choices=EXPENSE_CATEGORIES,
        validators=[DataRequired(message="Category is required.")],
    )
    description = TextAreaField(
        "Description",
        validators=[
            Optional(),
            Length(max=2000, message="Description must be 2000 characters or fewer."),
        ],
    )
    expense_date = DateField(
        "Date",
        validators=[DataRequired(message="Date is required.")],
        format="%Y-%m-%d",
    )
    submit = SubmitField("Save Expense")

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def validate_amount(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError("Amount must be greater than zero.")

    def validate_expense_date(self, field):
        if self.trip and field.data:
            if field.data < self.trip.start_date or field.data > self.trip.end_date:
                raise ValidationError("Expense date must fall within the trip dates.")


class DeleteExpenseForm(FlaskForm):
    submit = SubmitField("Delete Expense")
