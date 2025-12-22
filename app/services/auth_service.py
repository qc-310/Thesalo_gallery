from datetime import datetime
from flask import session, current_app
from app.extensions import db
from app.models.auth import User
from sqlalchemy.exc import IntegrityError
import uuid6

class AuthService:
    def get_google_user_info(self, token):
        # This wrapper can be mocked in tests
        from app.extensions import oauth
        resp = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo', token=token)
        resp.raise_for_status()
        return resp.json()

    def login_or_register_google_user(self, user_info):
        """
        Log in a user or register them if they don't exist.
        user_info: dict from Google OIDC
        """
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name')
        picture = user_info.get('picture')

        if not email:
            raise ValueError("Email not provided by Google")

        # Check strict email allowlist if configured (Env or DB?)
        # For now, simplistic approach from legacy app can be integrated here or in blueprint
        
        user = db.session.execute(db.select(User).filter_by(google_id=google_id)).scalar_one_or_none()
        
        if not user:
            # Fallback: check by email to merge accounts if we supported multiple providers
            # But we only support Google, so let's stick to google_id or email
            user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

        if user:
            # Update info
            user.name = name
            user.avatar_url = picture
            if not user.google_id:
                user.google_id = google_id
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                avatar_url=picture
            )
            db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # Retry or fetch again
            user = db.session.execute(db.select(User).filter_by(google_id=google_id)).scalar_one_or_none()
            
        return user
