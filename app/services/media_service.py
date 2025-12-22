import os
import shutil
from pathlib import Path
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.media import Media
from app.models.auth import User, Family
from app.tasks.media_tasks import process_media_task
import uuid6
import magic

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

    def upload_media(self, file, family_id: uuid6.UUID, uploader: User):
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Invalid file or extension")
        
        filename = secure_filename(file.filename)
        file_type = self.get_file_type(filename)
        
        # Determine strict save path based on design: uploads/{family_id}/{yyyy}/{mm}/{filename}
        now = datetime.now()
        yyyy = now.strftime('%Y')
        mm = now.strftime('%m')
        
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        family_dir = upload_folder / str(family_id) / yyyy / mm
        family_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicate filename
        save_path = family_dir / filename
        if save_path.exists():
             stem = Path(filename).stem
             ext = Path(filename).suffix
             filename = f"{stem}_{uuid6.uuid7().hex[:8]}{ext}"
             save_path = family_dir / filename

        # Register in DB (Pending Status)
        # Note: We read file size effectively by saving it first? 
        # Or seeking end? Let's save chunks or use save() if it's FileStorage
        file.save(str(save_path))
        file_size = save_path.stat().st_size

        mime = magic.from_file(str(save_path), mime=True)
        
        media = Media(
            family_id=family_id,
            uploader_id=uploader.id,
            filename=str(save_path.relative_to(upload_folder)).replace('\\', '/'), # Store relative path
            original_filename=file.filename,
            mime_type=mime,
            file_size_bytes=file_size,
            status='processing'
        )
        db.session.add(media)
        db.session.commit()
        
        # Trigger Async Task
        process_media_task.delay(str(media.id))
        
        return media
    
    def get_family_media(self, family_id, limit=20, offset=0):
        return db.session.execute(
            db.select(Media).filter_by(family_id=family_id)
            .order_by(Media.created_at.desc())
            .limit(limit).offset(offset)
        ).scalars().all()
