
import pytest
from app.models.auth import User, Family
from app.extensions import db
import uuid6
from flask_login import login_user

def test_integration_family_create(client, app):
    """IT-FAM-001: Create Family (Normal)"""
    # Setup User
    with app.app_context():
        user = User(id=uuid6.uuid7(), email='admin@ex.com', name='Admin', google_id='999')
        db.session.add(user)
        db.session.commit()
        user_id = str(user.id) # Store ID
    
    # Login
    with client.session_transaction() as sess:
        sess['_user_id'] = user_id
        sess['_fresh'] = True

    # Action
    response = client.post('/family/create', data={'name': 'Integration Family'}, follow_redirects=True)
    
    # Assert
    assert response.status_code == 200
    assert b'Integration Family' in response.data
    
    # Verify DB
    with app.app_context():
        # Re-query user to avoid detached instance
        user = db.session.get(User, uuid6.UUID(user_id))
        fam = db.session.execute(db.select(Family).filter_by(name='Integration Family')).scalar_one()
        assert fam is not None
        assert len(fam.members) == 1
        assert fam.members[0].user_id == user.id

def test_integration_family_list(client, app):
    """IT-FAM-002: Family List"""
    # Setup Data
    user_id = None
    with app.app_context():
        user = User(id=uuid6.uuid7(), email='user@ex.com', name='User', google_id='888')
        fam1 = Family(id=uuid6.uuid7(), name='Fam 1')
        fam2 = Family(id=uuid6.uuid7(), name='Fam 2')
        db.session.add_all([user, fam1, fam2])
        db.session.commit()
        
        user_id = str(user.id)
        fam1_id = fam1.id
        fam2_id = fam2.id
        
        # Add member (Using Service logic or Direct DB)
        from app.models.auth import FamilyMember
        m1 = FamilyMember(family_id=fam1_id, user_id=user.id, role='admin')
        m2 = FamilyMember(family_id=fam2_id, user_id=user.id, role='member')
        db.session.add_all([m1, m2])
        db.session.commit()

    # Login
    with client.session_transaction() as sess:
        sess['_user_id'] = user_id
        sess['_fresh'] = True

    # Action
    response = client.get('/family/list')
    
    # Assert
    assert response.status_code == 200
    assert b'Fam 1' in response.data
    assert b'Fam 2' in response.data
