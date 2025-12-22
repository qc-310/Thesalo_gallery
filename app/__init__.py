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
    from .blueprints.media import media_bp
    from .blueprints.core import core_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(family_bp, url_prefix='/family')
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(core_bp)

    # Celery Init
    from .celery_utils import celery_init_app
    app.config.from_mapping(
        CELERY=dict(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_ignore_result=True,
        ),
    )
    celery_init_app(app)

    return app

