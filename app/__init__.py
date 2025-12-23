from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, oauth

def create_app(config_name=None):
    if config_name is None:
        config_name = 'default'
        
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Import models to ensure they are discovered by Alembic
    from app import models

    # Register Blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.media import media_bp
    from .blueprints.core import core_bp
    from .blueprints.pets import pets_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # Family blueprint removed
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(core_bp)
    app.register_blueprint(pets_bp, url_prefix='/pets')

    # Configure Login Manager
    login_manager.login_view = 'auth.login_page'

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

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    from app.utils.filters import friendly_date
    app.jinja_env.filters['friendly_date'] = friendly_date

    return app

