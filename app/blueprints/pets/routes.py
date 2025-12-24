from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils.decorators import role_required
from app.services import PetService

pets_bp = Blueprint('pets', __name__)
pet_service = PetService()

@pets_bp.route('/', methods=['GET'])
@login_required
def list_pets():
    pets = pet_service.get_all_pets()
    return render_template('pets.html', pets=pets)

@pets_bp.route('/add', methods=['POST'])
@login_required
@role_required('family')
def add_pet():
    data = {
        'name': request.form.get('name'),
        'type': request.form.get('type'),
        'breed': request.form.get('breed'),
        'gender': request.form.get('gender'),
        'birth_date': request.form.get('birth_date'),
        'adoption_date': request.form.get('adoption_date'),
        'description': request.form.get('description')
    }
    
    avatar_file = request.files.get('avatar')
    
    try:
        pet_service.create_pet(data, avatar_file)
        flash('新しいペットを追加しました', 'success')
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        
    return redirect(url_for('pets.list_pets'))

@pets_bp.route('/<string:pet_id>/update', methods=['POST'])
@login_required
@role_required('family')
def update_pet(pet_id):
    data = {
        'name': request.form.get('name'),
        'type': request.form.get('type'),
        'breed': request.form.get('breed'),
        'gender': request.form.get('gender'),
        'birth_date': request.form.get('birth_date'),
        'adoption_date': request.form.get('adoption_date'),
        'description': request.form.get('description')
    }
    
    avatar_file = request.files.get('avatar')
    
    try:
        pet_service.update_pet(pet_id, data, avatar_file)
        flash('ペット情報を更新しました', 'success')
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        
    return redirect(url_for('pets.list_pets'))
