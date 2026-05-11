from flask import Blueprint, render_template

cars = Blueprint("cars", __name__)

@cars.route("/cars")
def cars_list():
    return render_template("cars.html")
