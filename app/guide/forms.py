from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

SECTION_CHOICES = [
    ("hotel",     "Hotel"),
    ("flight",    "Flight"),
    ("transfer",  "Transfer"),
    ("booking",   "Booking ID"),
    ("contact",   "Emergency Contact"),
    ("note",      "Travel Note"),
    ("rule",      "Do's & Don'ts"),
    ("etiquette", "Travel Etiquette"),
]

SECTION_PLACEHOLDERS = {
    "hotel":     ("Hotel name", "Address", "Phone", "Check-in date", "Check-out date"),
    "flight":    ("Flight number", "Route (e.g. JFK → LHR)", "Departure time", "Arrival time", "Terminal"),
    "transfer":  ("Transfer name", "Pickup location", "Drop-off location", "Reporting time", "Vehicle type"),
    "booking":   ("Service name", "Booking / reservation ID", "Confirmation number", "", ""),
    "contact":   ("Name / organisation", "Phone number", "Email / secondary contact", "", ""),
    "note":      ("Heading", "", "", "", ""),
    "rule":      ("Heading", "", "", "", ""),
    "etiquette": ("Heading", "", "", "", ""),
}


class GuideEntryForm(FlaskForm):
    section = SelectField(
        "Section",
        choices=SECTION_CHOICES,
        validators=[DataRequired()],
    )
    title = StringField(
        "Title / Name",
        validators=[DataRequired(), Length(max=160)],
    )
    subtitle = StringField("Address / Route / Organisation", validators=[Optional(), Length(max=200)])
    detail1  = StringField("Phone / Departure / Pickup / Reference", validators=[Optional(), Length(max=200)])
    detail2  = StringField("Check-in / Arrival / Drop-off", validators=[Optional(), Length(max=200)])
    detail3  = StringField("Check-out / Terminal / Reporting time", validators=[Optional(), Length(max=200)])
    body     = TextAreaField("Notes / Content", validators=[Optional(), Length(max=4000)])
    maps_query = StringField("Maps Search Query (optional)", validators=[Optional(), Length(max=300)])
    sort_order = StringField("Sort order", validators=[Optional()])
    submit = SubmitField("Save Entry")


class DeleteGuideEntryForm(FlaskForm):
    submit = SubmitField("Delete Entry")
