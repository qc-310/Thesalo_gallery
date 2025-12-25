from flask import Blueprint, redirect, url_for, session, render_template, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import oauth, login_manager, db
from app.services import AuthService
from app.models.auth import User
from app.utils.decorators import role_required
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
    return redirect(url_for('core.index')) # Index will likely redirect to login if not auth

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
    from flask import current_app
    bypass = current_app.config.get('BYPASS_AUTH', False)
    return render_template('login.html', bypass_auth=bypass)

@auth_bp.route('/dev/login', methods=['GET'])
def dev_login():
    from flask import current_app
    if not current_app.config.get('BYPASS_AUTH'):
         return "Not allowed", 403
    
    # Create or Get dummy user
    email = request.args.get('email', 'owner@example.com')
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid6.uuid7(),
            email=email,
            name='Dev Owner',
            google_id=f'dev_{uuid6.uuid7()}',
            avatar_url=None,
            role='owner' # Force owner role
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    flash(f'Logged in as Dev Owner ({email})', 'success')
    return redirect(url_for('core.index'))

@auth_bp.route('/users')
@login_required
@role_required('owner')
def list_users():
    users = db.session.execute(db.select(User).order_by(User.role, User.email)).scalars().all()
    return render_template('users.html', users=users)

@auth_bp.route('/users/<uuid_id>/role', methods=['POST'])
@login_required
@role_required('owner')
def update_role(uuid_id):
    try:
        user = db.session.get(User, uuid6.UUID(uuid_id))
    except (ValueError, TypeError):
        # Handle string UUID if necessary or rely on flask converter? 
        # Using string argument but converting manually to be safe
        user = db.session.get(User, uuid6.UUID(uuid_id))
        
    if not user:
        flash('ユーザーが見つかりません', 'error')
        return redirect(url_for('auth.list_users'))

    if user.id == current_user.id:
        flash('自分自身の権限は変更できません', 'error')
        return redirect(url_for('auth.list_users'))
        
    new_role = request.form.get('role')
    if new_role not in ['family', 'guest']:
        flash('不正なロールです', 'error')
        return redirect(url_for('auth.list_users'))
    
    user.role = new_role
    db.session.commit()
    flash(f'ユーザー {user.name} のロールを {new_role} に変更しました', 'success')
    return redirect(url_for('auth.list_users'))
