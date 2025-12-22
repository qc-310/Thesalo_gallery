from flask import Blueprint, request, jsonify, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from app.services import MediaService, FamilyService
import uuid6

media_bp = Blueprint('media', __name__)
media_service = MediaService()
family_service = FamilyService()

@media_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    # Attempt to get family_id from form, else default to user's first family
    family_id_str = request.form.get('family_id')
    family = None
    
    families = family_service.get_user_families(current_user.id)
    if not families:
        return jsonify({'error': 'No family found'}), 400

    if family_id_str:
        # Verify user belongs to this family
        try:
            req_fid = uuid6.UUID(family_id_str)
            for f in families:
                if f.id == req_fid:
                    family = f
                    break
        except:
            pass
    
    if not family:
        family = families[0] # Default
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    files = request.files.getlist('file')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
        try:
            media = media_service.upload_media(file, family.id, current_user)
            results.append({
                'id': str(media.id),
                'filename': media.filename,
                'status': media.status
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Upload error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
             
    return jsonify({'uploaded': results})

@media_bp.route('/file/<path:filename>')
@login_required
def serve_file(filename):
    # TODO: Add strict permission check (does user belong to family in filename path?)
    # filename likely starts with family_uuid/...
    # For now, strict login required is enforced.
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@media_bp.route('/thumb/<path:filename>')
@login_required
def serve_thumbnail(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
