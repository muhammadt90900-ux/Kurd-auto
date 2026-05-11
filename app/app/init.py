from flask import Flask

def create_app():

    app = Flask(__name__)

    from app.auth.routes import auth
    from app.cars.routes import cars
    from app.main.routes import main

    app.register_blueprint(auth)
    app.register_blueprint(cars)
    app.register_blueprint(main)

    return app
