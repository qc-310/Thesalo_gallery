
import pytest
from unittest.mock import MagicMock, patch
from app.tasks.media_tasks import process_media_task
from app.models.media import Media
from app.models.auth import User, Family
from app.extensions import db
import uuid6

def test_process_media_task_image(app, mocker):
    """UT-TASK-001: Resize Image"""
    with app.app_context():
        # Setup DB Dependencies
        user = User(id=uuid6.uuid7(), email='tester@example.com', name='Tester', google_id='123')
        family = Family(id=uuid6.uuid7(), name='Test Family')
        db.session.add(user)
        db.session.add(family)
        db.session.commit()

        # Setup DB Record
        media_id = uuid6.uuid7()
        media = Media(
            id=media_id,
            family_id=family.id,
            uploader_id=user.id,
            filename='path/to/image.jpg',
            original_filename='image.jpg',
            mime_type='image/jpeg',
            file_size_bytes=1000,
            status='processing'
        )
        db.session.add(media)
        db.session.commit()
        
        # Mocks
        mock_img = MagicMock()
        mock_img.__enter__.return_value = mock_img
        mock_img.size = (3000, 2000)
        mock_img.width = 3000
        mock_img.height = 2000
        mock_img._getexif.return_value = None # No EXIF
        mock_img.resize.return_value = mock_img
        mock_img.convert.return_value = mock_img
        
        mock_open = mocker.patch('PIL.Image.open', return_value=mock_img)
        # Mock ImageOps.exif_transpose to return the image itself
        mocker.patch('PIL.ImageOps.exif_transpose', return_value=mock_img)
        # Mock file existence
        mocker.patch('pathlib.Path.exists', return_value=True)
        
        # Action
        process_media_task(str(media_id))
        
        # Reload
        db.session.refresh(media)
        
        # Assertions
        mock_open.assert_called()
        # Expect resize to (1920, 1280) because 3000x2000 scaled to max 1920 width
        args, _ = mock_img.resize.call_args
        assert args[0] == (1920, 1280)
        mock_img.save.assert_called()
        assert media.status == 'ready'

def test_process_media_task_video(app, mocker):
    """UT-TASK-002: Video Thumbnail"""
    with app.app_context():
        # Setup DB Dependencies
        user = User(id=uuid6.uuid7(), email='tester2@example.com', name='Tester2', google_id='456')
        family = Family(id=uuid6.uuid7(), name='Test Family 2')
        db.session.add(user)
        db.session.add(family)
        db.session.commit()

        # Setup DB Record
        media_id = uuid6.uuid7()
        media = Media(
            id=media_id,
            family_id=family.id,
            uploader_id=user.id,
            filename='path/to/video.mp4',
            original_filename='video.mp4',
            mime_type='video/mp4',
            file_size_bytes=5000,
            status='processing'
        )
        db.session.add(media)
        db.session.commit()
        
        # Mocks
        mocker.patch('PIL.Image.open') # Not used for video path but just in case
        mock_run = mocker.patch('subprocess.run')
        # Mock file existence and mkdir
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('pathlib.Path.mkdir')
        
        # Action
        process_media_task(str(media_id))
        
        # Reload
        db.session.refresh(media)
        
        # Assertions
        mock_run.assert_called() # ffmpeg called
        assert media.status == 'ready'
        assert media.thumbnail_path is not None
        assert media.thumbnail_path.endswith('.jpg')
