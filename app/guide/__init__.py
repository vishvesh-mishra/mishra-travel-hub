from flask import Blueprint

bp = Blueprint("guide", __name__, url_prefix="/guide")

from . import routes  # noqa: E402, F401
