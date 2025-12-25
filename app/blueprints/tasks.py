import os
import shutil
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.media import Media
from google.cloud import storage
import uuid6
from PIL import Image, ImageOps
import pillow_heif
import subprocess
import magic

tasks_bp = Blueprint('tasks', __name__)

pillow_heif.register_heif_opener()

@tasks_bp.route('/handlers/process-media', methods=['POST'])
def process_media():
    payload = request.get_json()
    if not payload or 'media_id' not in payload:
        return jsonify({'error': 'Missing media_id'}), 400
        
    media_id = payload['media_id']
    print(f"Propcessing task for media_id: {media_id}")
    
    # Process
    try:
        _process_media_logic(media_id)
    except Exception as e:
        print(f"Error processing media {media_id}: {e}")
        # Return 200 to acknowledge task (so it doesn't retry infinitely if fatal error)
        # Or 500 to retry? 
        # For now, let's return 200 but mark as error in DB
        return jsonify({'status': 'error', 'message': str(e)}), 200
        
    return jsonify({'status': 'success'}), 200

def _process_media_logic(media_id_str):
    media = db.session.get(Media, uuid6.UUID(media_id_str))
    if not media:
        print(f"Media not found: {media_id_str}")
        return

    is_gcs = current_app.config['STORAGE_BACKEND'] == 'gcs'
    bucket = None
    
    if is_gcs:
        storage_client = storage.Client()
        bucket_name = current_app.config['GCS_BUCKET_NAME']
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(media.filename)
        
        if not blob.exists():
            print(f"GCS object not found: {media.filename}")
            media.status = 'error'
            db.session.commit()
            return
    else:
        # Local
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)
        if not os.path.exists(full_path):
            print(f"Local file not found: {full_path}")
            media.status = 'error'
            db.session.commit()
            return

    # Create Temp Dir
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_filename = Path(media.filename).name
        local_file_path = temp_path / local_filename
        
        # Download / Copy
        if is_gcs:
            bucket.blob(media.filename).download_to_filename(str(local_file_path))
        else:
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)
            shutil.copy(full_path, local_file_path)
        
        # Process
        updated = False
        
        if media.mime_type.startswith('image/'):
            updated = _process_image(media, local_file_path, bucket)
        elif media.mime_type.startswith('video/'):
            updated = _process_video(media, local_file_path, bucket)
            
        media.status = 'ready'
        db.session.commit()

def _process_image(media, file_path, bucket):
    with Image.open(file_path) as img:
        # EXIF Date
        exif = img._getexif()
        taken_at = None
        if exif:
             # 36867: DateTimeOriginal, 306: DateTime
            dt_str = exif.get(36867) or exif.get(306)
            if dt_str:
                try:
                    taken_at = dt_str.replace(":", "-", 2).replace(" ", "T")
                    media.taken_at = taken_at
                except:
                    pass
        
        # Resize/Convert
        max_size = 1920
        img = ImageOps.exif_transpose(img)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        ratio = min(1.0, max_size / max(img.size))
        if ratio < 1.0:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        media.width = img.width
        media.height = img.height
        
        # Save as JPEG
        current_ext = file_path.suffix.lower()
        new_filename = file_path.stem + ".jpg"
        new_file_path = file_path.parent / new_filename
        
        img.save(new_file_path, "JPEG", quality=85)
        
        # Upload back if changed/resized
        is_gcs = (bucket is not None)
        new_object_name = media.filename # default same
        
        if current_ext not in ['.jpg', '.jpeg']:
            # New extension
            p = Path(media.filename)
            new_object_name = str(p.parent / new_filename).replace('\\', '/')
            
            # Delete old
            if is_gcs:
                try:
                    bucket.blob(media.filename).delete()
                except: pass
            else:
                old_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)
                if os.path.exists(old_full_path):
                    os.remove(old_full_path)

            media.filename = new_object_name
            media.mime_type = 'image/jpeg'
        
        # Save new file
        if is_gcs:
            blob = bucket.blob(new_object_name)
            blob.upload_from_filename(str(new_file_path), content_type='image/jpeg')
        else:
            dest_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_object_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(new_file_path, dest_path)
        
    return True

def _process_video(media, file_path, bucket):
    # Thumbnail generation
    thumb_name = f"{file_path.stem}_thumb.jpg"
    thumb_path = file_path.parent / thumb_name
    
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(file_path),
        "-vframes", "1", "-q:v", "5", str(thumb_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if thumb_path.exists():
        p = Path(media.filename)
        thumb_object_name = str(p.parent / "thumbs" / thumb_name).replace('\\', '/')
        
        is_gcs = (bucket is not None)
        
        if is_gcs:
            blob = bucket.blob(thumb_object_name)
            blob.upload_from_filename(str(thumb_path), content_type='image/jpeg')
        else:
            dest_path = os.path.join(current_app.config['UPLOAD_FOLDER'], thumb_object_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(thumb_path, dest_path)
            
        media.thumbnail_path = thumb_object_name
        
    return True
