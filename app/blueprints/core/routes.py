from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services import MediaService, FamilyService

core_bp = Blueprint('core', __name__)
media_service = MediaService()
family_service = FamilyService()

@core_bp.route('/')
@login_required
def index():
    # Show media from first family for now
    families = family_service.get_user_families(current_user.id)
    if not families:
        return redirect(url_for('family.create_family'))
    
    media_list = media_service.get_family_media(families[0].id)
    return render_template('index.html', media_list=media_list, user=current_user)
