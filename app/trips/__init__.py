from flask import Blueprint


bp = Blueprint("trips", __name__, url_prefix="/trips")

from . import routes  # noqa: E402, F401
