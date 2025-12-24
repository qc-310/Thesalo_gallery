
import pytest
from app.models.auth import User, Family, FamilyMember
from app.models.media import Media
from app.extensions import db
import uuid6
import io

def test_integration_media_upload_normal(client, app):
    """IT-MEDIA-001: Upload Media (Normal)"""
    # Setup
    with app.app_context():
        user = User(id=uuid6.uuid7(), email='u@ex.com', name='U', google_id='111')
        fam = Family(id=uuid6.uuid7(), name='Media Fam')
        db.session.add_all([user, fam])
        
        mem = FamilyMember(family_id=fam.id, user_id=user.id, role='admin')
        db.session.add(mem)
        db.session.commit()
        fam_id = fam.id
        user_id = str(user.id)

    # Login
    with client.session_transaction() as sess:
        sess['_user_id'] = user_id
        sess['_fresh'] = True

    # File
    data = {
        'file': (io.BytesIO(b"fake image data"), 'test.jpg'),
        'family_id': str(fam_id)
    }
    
    # Action (We need to mock pure magic/validation if "fake image data" isn't valid jpeg, 
    # BUT this is Integration test. We should ideally use a minimal valid JPG or mock the validation service?
    # Test Spec says "Blackbox". So we should send valid data OR expect 400.
    # Let's verify VALIDATION failure first if data is fake.)
    
    # Wait, `python-magic` checks header. So "fake image data" might fail validation IT-MEDIA-002 equivalent.
    # To pass IT-MEDIA-001, we need valid headers.
    
    valid_jpg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C'
    data_valid = {
        'file': (io.BytesIO(valid_jpg_header + b' rest of data'), 'real.jpg'),
        'family_id': str(fam_id)
    }

    # Since pure integration hits Service which hits magic.from_buffer/file...
    # If we run in docker, we rely on real libs.
    # For now, let's try submitting.
    
    response = client.post('/media/upload', data=data_valid, content_type='multipart/form-data', follow_redirects=True)
    
    # Assert
    assert response.status_code == 200 # Or redirect to index
    # Check if flash message or content exists
    # If successful, should show index/timeline
    
    with app.app_context():
        media = db.session.execute(db.select(Media).filter_by(original_filename='real.jpg')).scalar_one_or_none()
        assert media is not None
        assert media.status == 'ready' or media.status == 'processing' # Task is Eager

def test_integration_media_upload_invalid(client, app):
    """IT-MEDIA-002: Upload Invalid Extension"""
    # Setup
    with app.app_context():
        user = User(id=uuid6.uuid7(), email='bad@ex.com', name='Bad', google_id='222')
        fam = Family(id=uuid6.uuid7(), name='Bad Fam')
        db.session.add_all([user, fam])
        mem = FamilyMember(family_id=fam.id, user_id=user.id, role='admin')
        db.session.add(mem)
        db.session.commit()
        fam_id = fam.id
        user_id = str(user.id)

    with client.session_transaction() as sess:
        sess['_user_id'] = user_id
        sess['_fresh'] = True

    data = {
        'file': (io.BytesIO(b"exe content"), 'malware.exe'),
        'family_id': str(fam_id)
    }
    
    response = client.post('/media/upload', data=data, content_type='multipart/form-data')
    
    # Assert
    # Usually 400 or Redirect with Flash "Invalid file"
    assert response.status_code in [400, 200, 302] 
    if response.status_code == 302 or response.status_code == 200:
         assert b'Invalid file' in response.data or b'Create Family' in response.data # Redirected/Flashed

    # Verify NO DB record
    with app.app_context():
        media = db.session.execute(db.select(Media).filter_by(original_filename='malware.exe')).scalar_one_or_none()
        assert media is None
