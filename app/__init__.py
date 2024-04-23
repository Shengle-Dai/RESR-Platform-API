from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy()
migrate = None


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Initialize Migration
    global migrate
    migrate = Migrate(app, db)

    # Import and register your blueprint after initializing db
    from app.routes import (
        user_blueprint,
        coating_blueprint,
        shape_blueprint,
        material_blueprint,
    )

    app.register_blueprint(user_blueprint, url_prefix="/api/users")
    app.register_blueprint(coating_blueprint, url_prefix="/api/coatings")
    app.register_blueprint(shape_blueprint, url_prefix="/api/shapes")
    app.register_blueprint(material_blueprint, url_prefix="/api/materials")

    return app
