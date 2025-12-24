import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE pet_profiles ADD COLUMN description TEXT;"))
            conn.commit()
            print("Successfully added 'description' column to 'pet_profiles' table.")
    except Exception as e:
        print(f"Error adding column (it might already exist): {e}")
