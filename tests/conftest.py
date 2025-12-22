import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "CELERY": {
             "broker_url": "memory://",
             "result_backend": "cache+memory://",
             "task_always_eager": True # Run tasks synchronously for testing
        },
        "GOOGLE_CLIENT_ID": "dummy_client_id",
        "GOOGLE_CLIENT_SECRET": "dummy_client_secret"
    })

    with app.app_context():
        # Prevent DetachedInstanceError in tests
        db.session.expire_on_commit = False
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
