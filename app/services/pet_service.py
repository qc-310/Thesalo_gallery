from app.extensions import db
from app.models.media import PetProfile
import uuid6
import os
from werkzeug.utils import secure_filename
from flask import current_app
from pathlib import Path

class PetService:
    def get_all_pets(self):
        return db.session.execute(db.select(PetProfile)).scalars().all()
        
    def get_pet(self, pet_id: str):
        try:
            return db.session.get(PetProfile, uuid6.UUID(pet_id))
        except:
            return None

    def _save_avatar(self, file) -> str:
        if not file or file.filename == '':
            return None
            
        filename = secure_filename(file.filename)
        # Unique filename
        stem = Path(filename).stem
        ext = Path(filename).suffix
        filename = f"pet_avatar_{uuid6.uuid7().hex[:8]}{ext}"
        
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        avatars_dir = upload_folder / 'avatars'
        avatars_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = avatars_dir / filename
        file.save(str(save_path))
        
        return str(save_path.relative_to(upload_folder)).replace('\\', '/')
            
    def create_pet(self, data: dict, avatar_file=None):
        avatar_url = self._save_avatar(avatar_file)
        
        pet = PetProfile(
            name=data.get('name'),
            type=data.get('type'),
            breed=data.get('breed'),
            gender=data.get('gender'),
            birth_date=data.get('birth_date'),
            adoption_date=data.get('adoption_date'),
            description=data.get('description'),
            avatar_url=avatar_url
        )
        db.session.add(pet)
        db.session.commit()
        return pet
        
    def update_pet(self, pet_id: str, data: dict, avatar_file=None):
        pet = self.get_pet(pet_id)
        if not pet:
            return None
            
        pet.name = data.get('name', pet.name)
        pet.type = data.get('type', pet.type)
        pet.breed = data.get('breed', pet.breed)
        pet.gender = data.get('gender', pet.gender)
        pet.birth_date = data.get('birth_date', pet.birth_date)
        pet.adoption_date = data.get('adoption_date', pet.adoption_date)
        pet.description = data.get('description', pet.description)
        
        if avatar_file:
            new_avatar = self._save_avatar(avatar_file)
            if new_avatar:
                pet.avatar_url = new_avatar
        
        db.session.commit()
        return pet
