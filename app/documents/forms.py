from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL


DOCUMENT_CATEGORIES = [
    ("Passport", "Passport"),
    ("Visa", "Visa"),
    ("Flight", "Flight"),
    ("Hotel", "Hotel"),
    ("Match Ticket", "Match Ticket"),
    ("Insurance", "Insurance"),
    ("Other", "Other"),
]


class DocumentForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=160, message="Title must be 160 characters or fewer."),
        ],
    )
    category = SelectField(
        "Category",
        choices=DOCUMENT_CATEGORIES,
        validators=[DataRequired(message="Category is required.")],
    )
    external_url = URLField(
        "Google Drive Link",
        validators=[
            Optional(),
            URL(message="Enter a valid URL."),
            Length(max=500, message="URL must be 500 characters or fewer."),
        ],
    )
    notes = TextAreaField(
        "Notes",
        validators=[
            Optional(),
            Length(max=2000, message="Notes must be 2000 characters or fewer."),
        ],
    )
    submit = SubmitField("Save Document")


class DeleteDocumentForm(FlaskForm):
    submit = SubmitField("Delete Document")
