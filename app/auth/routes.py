from flask import render_template

from . import bp


@bp.route("/login")
def login():
    return render_template("auth/login.html", title="Login")
