from flask import Blueprint


bp = Blueprint("expenses", __name__, url_prefix="/expenses")

from . import routes  # noqa: E402, F401
