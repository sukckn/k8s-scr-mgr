from flask import Flask
from app.routes.routes import create_blueprint

def create_app():
    app= Flask(__name__)
    app.config.from_object('app.config.Config')  # Load config

    base_url= app.config.get('BASE_URL', '/')  # Default to / if not set
    pull_scr_bp= create_blueprint(base_url)

    # Register blueprints
    app.register_blueprint(pull_scr_bp)

    return app
