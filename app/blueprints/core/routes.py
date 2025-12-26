from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app.utils.decorators import role_required
from flask_login import login_required, current_user
from app.services import MediaService
import uuid6
import google.auth
from google.cloud import storage
from google.auth import impersonated_credentials
import os

core_bp = Blueprint('core', __name__)
media_service = MediaService()

@core_bp.route('/')
@login_required
def index():
    sort_by = request.args.get('sort', 'created_at_desc')
    filter_type = request.args.get('type', 'all')
    
    media_list = media_service.get_global_media(
        sort_by=sort_by, 
        filter_type=filter_type, 
        user_id=current_user.id
    )
    return render_template('index.html', media_list=media_list, user=current_user)

@core_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        from app.extensions import db
        import os
        from werkzeug.utils import secure_filename
        
        # Update text fields
        display_name = request.form.get('display_name')
        bio = request.form.get('bio')
        
        current_user.display_name = display_name
        current_user.bio = bio
        
        # Handle Avatar Upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(f"avatar_{current_user.id}_{uuid6.uuid6()}.png")
                
                if current_app.config.get('STORAGE_BACKEND') == 'gcs':
                    # GCS Logic - Inlined for minimal impact, eventually ensure this is shared
                    try:
                        credentials, project = google.auth.default()
                        sa_email = os.environ.get('SERVICE_ACCOUNT_EMAIL') or f"thesalo-app-sa@{current_app.config['GOOGLE_CLOUD_PROJECT']}.iam.gserviceaccount.com"
                        credentials = impersonated_credentials.Credentials(
                            source_credentials=credentials,
                            target_principal=sa_email,
                            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                            lifetime=3600
                        )
                        storage_client = storage.Client(credentials=credentials)
                        bucket_name = current_app.config['GCS_BUCKET_NAME']
                        bucket = storage_client.bucket(bucket_name)
                        blob = bucket.blob(f"avatars/{filename}")
                        file.seek(0)
                        blob.upload_from_file(file)
                        current_user.avatar_url = f"avatars/{filename}"
                    except Exception as e:
                        print(f"GCS Upload Error: {e}")
                        # Fallback or Error? 
                        # Giving error message is better
                        flash(f'アイコンのアップロードに失敗しました: {e}', 'error')
                        return redirect(url_for('core.profile'))
                else:
                    # Save to uploads folder (make sure to use absolute path provided by config)
                    # For local we might want avatars/ prefix too if we want consistence?
                    # Original code was root relative? os.path.join(UPLOAD_FOLDER, filename)
                    # Let's keep original local behavior but maybe prefix with avatars/ for cleanness if I can?
                    # The original code: file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    # It saved directly to uploads/. I'll keep it as is to avoid breaking existing local avatars paths
                    # unless I move them.
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    current_user.avatar_url = filename
        
        try:
            db.session.commit()
            flash('プロフィールを更新しました', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'更新に失敗しました: {e}', 'error')
            
        return redirect(url_for('core.profile'))

    return render_template('profile.html', user=current_user)

@core_bp.route('/settings')
@login_required
@role_required('owner')
def settings():
    
    # Calculate Usage Stats (Media uploaded by current user)
    from app.models.media import Media
    from app.extensions import db
    from sqlalchemy import func
    
    stats = db.session.query(
        func.count(Media.id),
        func.sum(Media.file_size_bytes)
    ).filter(Media.uploader_id == current_user.id).first()
    
    media_count = stats[0] or 0
    total_bytes = stats[1] or 0
    
    # Format bytes
    if total_bytes < 1024 * 1024:
        storage_usage = f"{total_bytes / 1024:.1f} KB"
    elif total_bytes < 1024 * 1024 * 1024:
        storage_usage = f"{total_bytes / (1024 * 1024):.1f} MB"
    else:
        storage_usage = f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"

    return render_template('settings.html', user=current_user, media_count=media_count, storage_usage=storage_usage)
