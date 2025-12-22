
import pytest
from app.services import MediaService, FamilyService, AuthService
from app.models.media import Media
from unittest.mock import MagicMock
import io

def test_media_service_upload(app, mocker):
    with app.app_context():
        # Setup Services and User/Family
        auth = AuthService()
        family_svc = FamilyService()
        media_svc = MediaService()
        
        user = auth.login_or_register_google_user({
            'email': 'u@ex.com', 'sub': '000', 'name': 'U', 'picture': ''
        })
        family = family_svc.create_family("Fam", user)
        
        # Mock Task
        mock_task = mocker.patch('app.tasks.media_tasks.process_media_task.delay')
        
        # Create Dummy File
        data = b'fake image data'
        file = MagicMock()
        file.filename = 'test.jpg'
        file.read.return_value = data
        
        # Mock file.save to avoid disk write in unit test?
        # Ideally we use a temp dir via pytests tmp_path, 
        # but MediaService uses current_app.config['UPLOAD_FOLDER'].
        # Let's mock the save method on the file object or rely on app configuration.
        # Since logic calls file.save(path), we should mock file.save
        file.save = MagicMock()
        
        # We need to ensure the path calculation doesn't fail.
        # MediaService uses path.stat().st_size. This requires actual file on disk.
        # So we better use a real file or mock stat.
        
        # Let's use a real BytesIO/FileStorage that saves to a temp dir config in conftest?
        # conftest sets TESTING=True. Let's assume we can mock or use a temp folder.
        # For simplicity in this "Refactoring" task, let's mock stat and file.save.
        
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('pathlib.Path.exists', return_value=False)
        mocker.patch('pathlib.Path.stat', return_value=MagicMock(st_size=12345))
        mocker.patch('magic.from_file', return_value='image/jpeg')
        
        # Action
        media = media_svc.upload_media(file, family.id, user)
        
        # Assertions
        assert media.filename.endswith('test.jpg')
        assert media.status == 'processing'
        assert media.uploader_id == user.id
        assert media.mime_type == 'image/jpeg'
        
        # Task triggered?
        mock_task.assert_called_once()
