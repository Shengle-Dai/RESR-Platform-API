from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize SQLAlchemy and Migrate here
db = SQLAlchemy()
migrate = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    # Initialize Migrate here
    global migrate
    migrate = Migrate(app, db)

    # Import and register your blueprint after initializing db
    from app.routes import user_blueprint  # Moved inside create_app
    app.register_blueprint(user_blueprint, url_prefix='/api')

    return app
