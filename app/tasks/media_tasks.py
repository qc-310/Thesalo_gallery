import os
from celery import shared_task
from app.extensions import db
from app.models.media import Media
from PIL import Image, ImageOps
import pillow_heif
import uuid6
from pathlib import Path
from flask import current_app
import subprocess

# Register HEIF opener
pillow_heif.register_heif_opener()

@shared_task(ignore_result=True)
def process_media_task(media_id_str):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        media = db.session.get(Media, uuid6.UUID(media_id_str))
        if not media:
            return

        try:
            upload_folder = Path(app.config['UPLOAD_FOLDER'])
            # media.filename is relative path like "family_id/2025/12/file.jpg"
            file_path = upload_folder / media.filename
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # --- Image Processing ---
            if media.mime_type.startswith('image/'):
                _process_image(media, file_path)

            # --- Video Processing ---
            elif media.mime_type.startswith('video/'):
                _process_video(media, file_path)
            
            media.status = 'ready'
            db.session.commit()

        except Exception as e:
            media.status = 'error'
            print(f"Task Failed for {media_id_str}: {e}")
            db.session.commit()
            # In production, we might want to log this to a proper logger

def _process_image(media, file_path):
    with Image.open(file_path) as img:
        # 1. Extract EXIF Date
        exif = img._getexif()
        taken_at = None
        if exif:
            # 36867: DateTimeOriginal
            dt_str = exif.get(36867) or exif.get(306)
            if dt_str:
                try:
                    taken_at = dt_str.replace(":", "-", 2).split(" ")[0] # Just YYYY-MM-DD for now or full ISO?
                    # Design says captured_at in ISO format
                    taken_at = dt_str.replace(":", "-", 2).replace(" ", "T")
                except:
                    pass
        
        if taken_at:
            media.taken_at = taken_at

        # 2. Resize and Convert (Overwrite original for storage saving?)
        # Design constraint: Max 1920px width, JPEG q=85
        max_size = 1920
        img = ImageOps.exif_transpose(img) # Fix orientation
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        ratio = min(1.0, max_size / max(img.size))
        if ratio < 1.0:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Calculate dimensions
        media.width = img.width
        media.height = img.height
        
        # Save as JPEG (Overwrite if not video/other but even if png/heic we want jpeg)
        # If it was HEIC, filename change? 
        # Design: "HEIC images will be automatically converted to JPEG"
        # If we change extension, we must update media.filename and delete old file
        current_ext = file_path.suffix.lower()
        if current_ext != '.jpg' and current_ext != '.jpeg':
            new_path = file_path.with_suffix('.jpg')
            img.save(new_path, "JPEG", quality=85)
            # Delete old
            file_path.unlink()
            # Update DB path
            media.filename = str(new_path.relative_to(Path(current_app.config['UPLOAD_FOLDER']))).replace('\\', '/')
            media.mime_type = 'image/jpeg'
        else:
            img.save(file_path, "JPEG", quality=85)

def _process_video(media, file_path):
    # Generate Thumbnail
    thumb_dir = file_path.parent / "thumbs"
    thumb_dir.mkdir(exist_ok=True)
    thumb_name = f"{file_path.stem}_thumb.jpg"
    thumb_path = thumb_dir / thumb_name
    
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(file_path),
        "-vframes", "1", "-q:v", "5", str(thumb_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if thumb_path.exists():
        # Store relative thumbnail path
        media.thumbnail_path = str(thumb_path.relative_to(Path(current_app.config['UPLOAD_FOLDER']))).replace('\\', '/')
