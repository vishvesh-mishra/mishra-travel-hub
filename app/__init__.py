import os

from flask import Flask

from config import config_by_name

from .extensions import db, login_manager


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    selected_config = config_name or os.environ.get("FLASK_CONFIG", "default")
    app.config.from_object(config_by_name[selected_config])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from . import models  # noqa: F401

    register_blueprints(app)
    register_commands(app)

    return app


def register_blueprints(app):
    from .auth import bp as auth_bp
    from .documents import bp as documents_bp
    from .expenses import bp as expenses_bp
    from .journal import bp as journal_bp
    from .main import bp as main_bp
    from .shopping import bp as shopping_bp
    from .trips import bp as trips_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(journal_bp)


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Initialized the database.")
