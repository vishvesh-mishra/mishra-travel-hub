from flask import render_template

from . import bp


@bp.route("/")
def dashboard():
    return render_template("main/dashboard.html", title="Dashboard")
