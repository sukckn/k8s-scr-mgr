from flask import Flask
from app.routes.routes import create_blueprint
k8s_scr_mgr_version= '1.0'

def create_app():
    app= Flask(__name__)  
    print(f"K8S SCR Manager Service Version {k8s_scr_mgr_version}")

    app.config.from_object('app.config.Config')  # Load config

    base_url= app.config.get('BASE_URL', '/k8s-scr-mgr')  # Default to / if not set
    pull_scr_bp= create_blueprint(base_url, k8s_scr_mgr_version)

    # Register blueprints
    app.register_blueprint(pull_scr_bp)

    return app
