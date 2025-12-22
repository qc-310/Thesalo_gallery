from flask import Flask
import os

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuration will be loaded here
    app.config.from_object(os.environ.get('APP_SETTINGS', 'app.config.Config'))

    return app
