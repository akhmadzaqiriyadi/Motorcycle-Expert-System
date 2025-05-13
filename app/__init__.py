from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    
    with app.app_context():
        # Import and register routes
        from .routes import init_routes
        init_routes(app)  # Pass app to routes for registration
        db.create_all()  # Create tables
        
    return app