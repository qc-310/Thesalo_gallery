from app.extensions import db
from app.models.media import PetProfile
import uuid6
import os
from werkzeug.utils import secure_filename
from flask import current_app
from pathlib import Path
import google.auth
from google.cloud import storage
from google.auth import impersonated_credentials

class PetService:
    def get_all_pets(self):
        return db.session.execute(db.select(PetProfile)).scalars().all()
        
    def get_pet(self, pet_id: str):
        try:
            return db.session.get(PetProfile, uuid6.UUID(pet_id))
        except:
            return None

    def _get_storage_client(self):
        if current_app.config.get('STORAGE_BACKEND') == 'gcs':
             credentials, project = google.auth.default()
             sa_email = os.environ.get('SERVICE_ACCOUNT_EMAIL') or f"thesalo-app-sa@{current_app.config['GOOGLE_CLOUD_PROJECT']}.iam.gserviceaccount.com"
             
             try:
                 credentials = impersonated_credentials.Credentials(
                     source_credentials=credentials,
                     target_principal=sa_email,
                     target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                     lifetime=3600
                 )
             except Exception as e:
                 print(f"Warning: Failed to create impersonated credentials: {e}")

             return storage.Client(credentials=credentials)
        return None

    def _save_avatar(self, file) -> str:
        if not file or file.filename == '':
            return None
            
        filename = secure_filename(file.filename)
        # Unique filename
        stem = Path(filename).stem
        ext = Path(filename).suffix
        filename = f"pet_avatar_{uuid6.uuid7().hex[:8]}{ext}"
        
        # GCS Support
        if current_app.config.get('STORAGE_BACKEND') == 'gcs':
            storage_client = self._get_storage_client()
            bucket_name = current_app.config['GCS_BUCKET_NAME']
            bucket = storage_client.bucket(bucket_name)
            
            # Save to 'avatars/' prefix in bucket
            object_name = f"avatars/{filename}"
            blob = bucket.blob(object_name)
            
            file.seek(0)
            blob.upload_from_file(file)
            
            return object_name
            
        # Local Fallback
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
