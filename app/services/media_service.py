import os
from pathlib import Path
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.media import Media
from app.models.auth import User
import uuid6
import magic
from google.cloud import storage
from google.cloud import tasks_v2
import json
import google.auth
from google.auth import impersonated_credentials

class MediaService:
    def allowed_file(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".heic", ".mp4", ".mov", ".avi", ".mkv"}
        return ext in allowed_extensions

    def get_file_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext in {".png", ".jpg", ".jpeg", ".gif", ".heic"}:
            return "image"
        if ext in {".mp4", ".mov", ".avi", ".mkv"}:
            return "video"
        return "other"
        
    def _get_storage_client(self):
        # On Cloud Run, default credentials don't support signing.
        # We wrap them in ImpersonatedCredentials to use IAM API for signing.
        if current_app.config.get('STORAGE_BACKEND') == 'gcs':
             credentials, project = google.auth.default()
             sa_email = self._get_service_account_email()
             
             # Only wrap if we have a specific SA email to impersonate and we are likely in a non-key env
             # (Self-impersonation)
             if sa_email:
                 try:
                     credentials = impersonated_credentials.Credentials(
                         source_credentials=credentials,
                         target_principal=sa_email,
                         target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                         lifetime=3600
                     )
                 except Exception as e:
                     print(f"Warning: Failed to create impersonated credentials: {e}")
                     # Fallback to default if impersonation fails (e.g. local dev with key)

             return storage.Client(credentials=credentials)
             
        return storage.Client()

    def _get_tasks_client(self):
        return tasks_v2.CloudTasksClient()

    def upload_media(self, file, uploader: User, description: str = None):
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Invalid file or extension")
        
        filename = secure_filename(file.filename)
        
        # Determine global save path: galleries/{yyyy}/{mm}/{filename}
        now = datetime.now()
        yyyy = now.strftime('%Y')
        mm = now.strftime('%m')
        
        # Unique check loop
        base_name = Path(filename).stem
        ext = Path(filename).suffix
        counter = 0
        
        while True:
            if counter == 0:
                final_filename = filename
            else:
                final_filename = f"{base_name}_{counter}{ext}"
            
            # Object name (Relative path) used for DB
            object_name = f"galleries/{yyyy}/{mm}/{final_filename}"
            
            # Check existence
            if current_app.config['STORAGE_BACKEND'] == 'gcs':
                if not self._gcs_exists(object_name):
                    break
            else:
                 # Local
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], yyyy, mm, final_filename)
                if not os.path.exists(full_path):
                    break
            counter += 1

        # Upload/Save
        file.seek(0)
        header = file.read(2048)
        mime = magic.from_buffer(header, mime=True)
        file.seek(0) # Reset
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if current_app.config['STORAGE_BACKEND'] == 'gcs':
            self._save_to_gcs(file, object_name, mime)
        else:
            self._save_to_local(file, object_name)
        
        media = Media(
            uploader_id=uploader.id,
            filename=object_name, 
            original_filename=file.filename,
            mime_type=mime,
            file_size_bytes=file_size,
            status='processing',
            description=description
        )
        db.session.add(media)
        db.session.commit()
        
        # Trigger Task
        if current_app.config['TASK_RUNNER'] == 'sync':
            # Run directly
            from app.blueprints.tasks import _process_media_logic
            print(f"[Sync] Processing media {media.id} locally...")
            _process_media_logic(str(media.id))
        else:
            self._create_cloud_task(media.id)
        
        return media

    def _gcs_exists(self, object_name):
        storage_client = self._get_storage_client()
        bucket_name = current_app.config['GCS_BUCKET_NAME']
        bucket = storage_client.bucket(bucket_name)
        return bucket.blob(object_name).exists()
        
    def _save_to_gcs(self, file, object_name, mime_type):
        storage_client = self._get_storage_client()
        bucket_name = current_app.config['GCS_BUCKET_NAME']
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_file(file, content_type=mime_type)

    def generate_signed_url(self, object_name, expiration=3600):
        """Generate a signed URL for a GCS blob."""
        storage_client = self._get_storage_client()
        bucket_name = current_app.config['GCS_BUCKET_NAME']
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET"
        )

    def _save_to_local(self, file, object_name):
        # object_name = galleries/2023/12/foo.jpg
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], object_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)

    def _create_cloud_task(self, media_id):
        client = self._get_tasks_client()
        queue_path = current_app.config['CLOUD_TASKS_QUEUE_PATH']
        worker_url = current_app.config['CLOUD_RUN_SERVICE_URL']
        
        if not worker_url:
            # Fallback to request.host_url if available (handles dynamic domains)
            from flask import request
            if request:
                worker_url = request.host_url.rstrip('/')

        if not worker_url:
            print("Warning: CLOUD_RUN_SERVICE_URL not set and request context missing. Task not created.")
            return

        # Cloud Run Worker URL (e.g., https://service-url/handlers/process-media)
        url = f"{worker_url}/handlers/process-media"
        
        payload = {'media_id': str(media_id)}
        json_payload = json.dumps(payload).encode()

        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': url,
                'headers': {'Content-Type': 'application/json'},
                'body': json_payload,
                # Add OIDC token for authentication
                'oidc_token': {
                    'service_account_email': self._get_service_account_email()
                }
            }
        }
        
        try:
            client.create_task(parent=queue_path, task=task)
        except Exception as e:
            print(f"Failed to create cloud task: {e}")

    def _get_service_account_email(self):
        sa_email = os.environ.get('SERVICE_ACCOUNT_EMAIL')
        if sa_email:
            return sa_email
        return f"thesalo-app-sa@{current_app.config['GOOGLE_CLOUD_PROJECT']}.iam.gserviceaccount.com"

    def get_global_media(self, limit=20, offset=0, sort_by='created_at_desc', filter_type='all', user_id=None):
        query = db.select(Media)
        
        # Filter
        if filter_type == 'image':
            query = query.filter(Media.mime_type.like('image%'))
        elif filter_type == 'video':
            query = query.filter(Media.mime_type.like('video%'))
        elif filter_type == 'mine' and user_id:
            query = query.filter(Media.uploader_id == user_id)
        elif filter_type == 'favorites' and user_id:
            query = query.join(Media.favorited_by).filter(User.id == user_id)
            
        # Sort
        if sort_by == 'created_at_asc':
            query = query.order_by(Media.created_at.asc())
        elif sort_by == 'created_at_desc':
            query = query.order_by(Media.created_at.desc())
        elif sort_by == 'taken_at_desc':
            query = query.order_by(Media.taken_at.desc().nullslast(), Media.created_at.desc())
        elif sort_by == 'taken_at_asc':
            query = query.order_by(Media.taken_at.asc().nullslast(), Media.created_at.asc())
        else:
            # Default to created_at desc
            query = query.order_by(Media.created_at.desc())
            
        return db.session.execute(
            query.limit(limit).offset(offset)
        ).scalars().all()

    def get_media(self, media_id: str):
        try:
            return db.session.get(Media, uuid6.UUID(media_id))
        except:
            return None

    def delete_media(self, media: Media):
        if not media:
             return
             
        # Delete from Storage
        try:
            if current_app.config['STORAGE_BACKEND'] == 'gcs':
                storage_client = self._get_storage_client()
                bucket_name = current_app.config['GCS_BUCKET_NAME']
                bucket = storage_client.bucket(bucket_name)
                
                # Delete Original
                blob = bucket.blob(media.filename)
                if blob.exists():
                    blob.delete()
                    
                # Delete Thumbnail if exists
                if media.thumbnail_path:
                    thumb_blob = bucket.blob(media.thumbnail_path)
                    if thumb_blob.exists():
                        thumb_blob.delete()
            else:
                # Local Delete
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)
                if os.path.exists(full_path):
                    os.remove(full_path)
                if media.thumbnail_path:
                    thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.thumbnail_path)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)

        except Exception as e:
            print(f"Error deleting from storage: {e}")
                
        db.session.delete(media)
        db.session.commit()

    def toggle_favorite(self, media_id: str, user_id: uuid6.UUID) -> dict:
        media = self.get_media(media_id)
        user = db.session.get(User, user_id)
        
        if not media or not user:
            raise ValueError("Media or User not found")
            
        is_favorited = False
        if user in media.favorited_by:
            media.favorited_by.remove(user)
            is_favorited = False
        else:
            media.favorited_by.append(user)
            is_favorited = True
            
        db.session.commit()
        
        return {
            'media_id': str(media.id),
            'items': is_favorited # current state
        }
