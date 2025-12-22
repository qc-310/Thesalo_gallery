from flask import Blueprint, redirect, url_for, session, render_template, request, flash
from flask_login import login_user, logout_user, login_required
from app.extensions import oauth, login_manager, db
from app.services import AuthService
from app.models.auth import User
import uuid6

auth_bp = Blueprint('auth', __name__, template_folder='templates')
auth_service = AuthService()

@login_manager.user_loader
def load_user(user_id):
    try:
        # User ID is UUID string in session
        return db.session.get(User, uuid6.UUID(user_id))
    except:
        return None

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index')) # Index will likely redirect to login if not auth

@auth_bp.route('/callback')
def authorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = auth_service.get_google_user_info(token)
        user = auth_service.login_or_register_google_user(user_info)
        
        login_user(user)
        # Check if user has any family? If not redirect to family creation?
        # For now, redirect to index
        return redirect(url_for('core.index'))
    except Exception as e:
        flash(f'Login failed: {e}', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/login_page')
def login_page():
    return render_template('login.html')

@auth_bp.route('/dev/login', methods=['GET'])
def dev_login():
    from flask import current_app
    if not current_app.debug and not current_app.config.get('TESTING'):
         return "Not allowed", 403
    
    # Create or Get dummy user
    email = request.args.get('email', 'dev@example.com')
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid6.uuid7(),
            email=email,
            name='Dev User',
            google_id=f'dev_{uuid6.uuid7()}',
            avatar_url=None
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('core.index'))
