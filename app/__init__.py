from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, oauth

def create_app(config_name=None):
    if config_name is None:
        config_name = 'default'
        
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)

    # Import models to ensure they are discovered by Alembic
    from app import models

    # Register Blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.family import family_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(family_bp, url_prefix='/family')

    return app

