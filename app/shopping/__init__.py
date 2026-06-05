from flask import Blueprint


bp = Blueprint("shopping", __name__, url_prefix="/shopping")

from . import routes  # noqa: E402, F401
