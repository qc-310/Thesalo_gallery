import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB limit as per design
    
    # Auth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    

    # Job & Storage Configuration
    # 'gcs' or 'local'
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'gcs')
    # 'cloud_tasks' or 'sync'
    # 'cloud_tasks' or 'sync'
    TASK_RUNNER = os.environ.get('TASK_RUNNER', 'cloud_tasks')

    # Dev Login Bypass
    BYPASS_AUTH = os.environ.get('BYPASS_AUTH', 'false').lower() == 'true'
    
    # Local Storage Path (only used if STORAGE_BACKEND='local')
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'uploads')

    # GCP
    GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', 'thesalo-gallery')
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'thesalo-uploads-thesalo-gallery')
    CLOUD_TASKS_QUEUE_PATH = os.environ.get('CLOUD_TASKS_QUEUE_PATH', 'projects/thesalo-gallery/locations/us-west1/queues/image-processing-queue')
    CLOUD_RUN_SERVICE_URL = os.environ.get('CLOUD_RUN_SERVICE_URL') # For worker callback

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Specific production settings can go here

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
