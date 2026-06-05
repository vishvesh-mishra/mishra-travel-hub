from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class TripForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Trip name is required."),
            Length(max=120, message="Trip name must be 120 characters or fewer."),
        ],
    )
    destination = StringField(
        "Destination",
        validators=[
            DataRequired(message="Destination is required."),
            Length(max=160, message="Destination must be 160 characters or fewer."),
        ],
    )
    start_date = DateField(
        "Start Date",
        validators=[DataRequired(message="Start date is required.")],
        format="%Y-%m-%d",
    )
    end_date = DateField(
        "End Date",
        validators=[DataRequired(message="End date is required.")],
        format="%Y-%m-%d",
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=2000, message="Notes must be 2000 characters or fewer.")],
    )
    submit = SubmitField("Save Trip")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date must be on or after the start date.")


class DeleteTripForm(FlaskForm):
    submit = SubmitField("Delete Trip")


class ItineraryItemForm(FlaskForm):
    date = DateField(
        "Date",
        validators=[DataRequired(message="Date is required.")],
        format="%Y-%m-%d",
    )
    time = TimeField(
        "Time",
        validators=[DataRequired(message="Time is required.")],
        format="%H:%M",
    )
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=160, message="Title must be 160 characters or fewer."),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[
            Optional(),
            Length(max=2000, message="Description must be 2000 characters or fewer."),
        ],
    )
    submit = SubmitField("Save Itinerary Item")

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def validate_date(self, field):
        if self.trip and field.data:
            if field.data < self.trip.start_date or field.data > self.trip.end_date:
                raise ValidationError("Date must be within the trip dates.")


class DeleteItineraryItemForm(FlaskForm):
    submit = SubmitField("Delete Itinerary Item")
