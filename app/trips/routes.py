from flask import render_template

from . import bp


@bp.route("/")
def index():
    return render_template("trips/index.html", title="Trips")


@bp.route("/<int:trip_id>")
def detail(trip_id):
    return render_template("trips/detail.html", title="Trip Detail", trip_id=trip_id)


@bp.route("/<int:trip_id>/itinerary")
def itinerary(trip_id):
    return render_template("trips/itinerary.html", title="Itinerary", trip_id=trip_id)
