import os
import shutil
from pathlib import Path
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.media import Media
from app.models.auth import User
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

    def upload_media(self, file, uploader: User, description: str = None):
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Invalid file or extension")
        
        filename = secure_filename(file.filename)
        file_type = self.get_file_type(filename)
        
        # Determine global save path: uploads/galleries/{yyyy}/{mm}/{filename}
        now = datetime.now()
        yyyy = now.strftime('%Y')
        mm = now.strftime('%m')
        
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        # Changed to 'galleries' to distinguish from previous structure if needed, or just root
        # Let's use 'galleries' as a namespace
        gallery_dir = upload_folder / 'galleries' / yyyy / mm
        gallery_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicate filename
        save_path = gallery_dir / filename
        if save_path.exists():
             stem = Path(filename).stem
             ext = Path(filename).suffix
             filename = f"{stem}_{uuid6.uuid7().hex[:8]}{ext}"
             save_path = gallery_dir / filename

        # Register in DB (Pending Status)
        file.save(str(save_path))
        file_size = save_path.stat().st_size

        mime = magic.from_file(str(save_path), mime=True)
        
        media = Media(
            uploader_id=uploader.id,
            filename=str(save_path.relative_to(upload_folder)).replace('\\', '/'), # Store relative path
            original_filename=file.filename,
            mime_type=mime,
            file_size_bytes=file_size,
            status='processing',
            description=description
        )
        db.session.add(media)
        db.session.commit()
        
        # Trigger Async Task
        process_media_task.delay(str(media.id))
        
        return media
    
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
        # Delete file from filesystem
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / media.filename
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass # Already deleted or permission error
                
        # Delete thumbnail if exists (assuming standard loc)
        # To strictly clean, we should look for existing thumb task or property
        # For now, let's remove from DB
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
