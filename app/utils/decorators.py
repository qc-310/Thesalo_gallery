from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(roles):
    """
    Decorator to restrict access to specific roles.
    roles: str or list of allowed roles.
    """
    if not isinstance(roles, list):
        roles = [roles]

    def decoration(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login_page'))
            
            # Expanded checks for hierarchy
            # If 'family' is allowed, 'owner' should also be allowed implicitly
            # Simple approach: define accepted roles for each requirement
            
            allowed = False
            user_role = getattr(current_user, 'role', 'guest')

            if user_role in roles:
                allowed = True
            
            # Hierarchy Logic: Owner has access to everything Family has
            if 'family' in roles and user_role == 'owner':
                allowed = True

            if not allowed:
                flash("This action is restricted.", "warning")
                return redirect(url_for('core.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decoration
