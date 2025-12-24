from flask import Blueprint, request, jsonify, send_from_directory, current_app, abort, render_template
from flask_login import login_required, current_user
from app.services import MediaService
from app.utils.decorators import role_required
import uuid6

media_bp = Blueprint('media', __name__)
media_service = MediaService()

@media_bp.route('/add', methods=['GET'])
@login_required
@role_required('family')
def upload_page():
    return render_template('upload.html')

@media_bp.route('/upload', methods=['POST'])
@login_required
@role_required('family')
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    files = request.files.getlist('file')
    comments = request.form.getlist('comments')
    results = []
    
    for i, file in enumerate(files):
        if file.filename == '':
            continue
        try:
            # Get description by index if available
            description = comments[i] if i < len(comments) else None
            
            # Upload global media using current user as uploader
            media = media_service.upload_media(file, current_user, description=description)
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

@media_bp.route('/<string:media_id>/update', methods=['POST'])
@login_required
@role_required('family')
def update_media(media_id):
    from app.services import MediaService
    from app.extensions import db
    
    try:
        media = media_service.get_media(media_id)
        if not media:
            return jsonify({'error': 'Media not found'}), 404
            
        # Permission check: Uploader OR Family Admin (simplified to just uploader/member logic for now)
        # Ideally check if current_user in media.family.members
        
        description = request.form.get('description')
        taken_at = request.form.get('taken_at')
        
        media.description = description
        media.taken_at = taken_at
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@media_bp.route('/<string:media_id>/delete', methods=['POST'])
@login_required
@role_required('owner')
def delete_media_item(media_id):
    media = media_service.get_media(media_id)
    if not media:
        return jsonify({'error': 'Media not found'}), 404
        
    if media.uploader_id != current_user.id:
        # Check if family owner? For now only uploader can delete
        return jsonify({'error': 'Permission denied'}), 403
        
    try:
        media_service.delete_media(media)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/<string:media_id>/details', methods=['GET'])
@login_required
def get_media_details(media_id):
    from app.services import MediaService
    media = media_service.get_media(media_id)
    if not media:
        return jsonify({'error': 'Not found'}), 404
        
    return jsonify({
        'id': str(media.id),
        'description': media.description,
        'taken_at': media.taken_at,
        'filename': media.filename,
        'mime_type': media.mime_type,
        'thumbnail_path': media.thumbnail_path
    })

@media_bp.route('/<string:media_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(media_id):
    try:
        result = media_service.toggle_favorite(media_id, current_user.id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
