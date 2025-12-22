from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import FamilyService

family_bp = Blueprint('family', __name__)
family_service = FamilyService()

@family_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_family():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            family = family_service.create_family(name, current_user)
            flash(f'Family "{family.name}" created!', 'success')
            return redirect(url_for('core.index')) # Redirect to dash/index
    return render_template('create_family.html')

@family_bp.route('/list')
@login_required
def list_families():
    families = family_service.get_user_families(current_user.id)
    return render_template('list_families.html', families=families)
