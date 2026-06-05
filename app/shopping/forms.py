from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


SHOPPING_CATEGORIES = [
    ("Clothing", "Clothing"),
    ("Electronics", "Electronics"),
    ("Souvenirs", "Souvenirs"),
    ("Gifts", "Gifts"),
    ("Food", "Food"),
    ("Other", "Other"),
]


class ShoppingItemForm(FlaskForm):
    item_name = StringField(
        "Item Name",
        validators=[
            DataRequired(message="Item name is required."),
            Length(max=160, message="Item name must be 160 characters or fewer."),
        ],
    )
    category = SelectField(
        "Category",
        choices=SHOPPING_CATEGORIES,
        validators=[DataRequired(message="Category is required.")],
    )
    notes = TextAreaField(
        "Notes",
        validators=[
            Optional(),
            Length(max=2000, message="Notes must be 2000 characters or fewer."),
        ],
    )
    completed = BooleanField("Completed")
    submit = SubmitField("Save Shopping Item")


class DeleteShoppingItemForm(FlaskForm):
    submit = SubmitField("Delete Shopping Item")


class ToggleShoppingItemForm(FlaskForm):
    submit = SubmitField("Toggle")
