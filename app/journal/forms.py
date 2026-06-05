from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class JournalEntryForm(FlaskForm):
    entry_date = DateField(
        "Date",
        validators=[DataRequired(message="Date is required.")],
        format="%Y-%m-%d",
    )
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=160, message="Title must be 160 characters or fewer."),
        ],
    )
    content = TextAreaField(
        "Content",
        validators=[
            DataRequired(message="Content is required."),
            Length(max=10000, message="Content must be 10000 characters or fewer."),
        ],
    )
    submit = SubmitField("Save Entry")

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def validate_entry_date(self, field):
        if self.trip and field.data:
            if field.data < self.trip.start_date or field.data > self.trip.end_date:
                raise ValidationError("Entry date must fall within the trip dates.")


class DeleteJournalEntryForm(FlaskForm):
    submit = SubmitField("Delete Entry")
