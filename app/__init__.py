from flask import Flask
from .extensions import db, login_manager

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "change-this"
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"

    db.init_app(app)
    login_manager.init_app(app)

    from .auth.routes import auth
    from .cars.routes import cars
    from .main.routes import main

    app.register_blueprint(auth)
    app.register_blueprint(cars)
    app.register_blueprint(main)

    return app
