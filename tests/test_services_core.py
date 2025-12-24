
import pytest
from app.services import AuthService, FamilyService
from app.models.auth import User, Family, FamilyMember
import uuid6

def test_auth_service(app):
    with app.app_context():
        service = AuthService()
        
        # Test: Register new user
        user_info = {
            'email': 'test@example.com',
            'sub': 'google_123',
            'name': 'Test User',
            'picture': 'http://example.com/pic.jpg'
        }
        
        user = service.login_or_register_google_user(user_info)
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.google_id == 'google_123'
        
        # Test: Login existing user (update info)
        user_info['name'] = 'Updated Name'
        user_updated = service.login_or_register_google_user(user_info)
        assert user_updated.id == user.id
        assert user_updated.name == 'Updated Name'

def test_family_service(app):
    with app.app_context():
        auth_service = AuthService()
        family_service = FamilyService()
        
        # Setup User
        user = auth_service.login_or_register_google_user({
            'email': 'dad@example.com', 'sub': '111', 'name': 'Dad', 'picture': ''
        })
        
        # Test: Create Family
        family = family_service.create_family("My Family", user)
        assert family.name == "My Family"
        assert len(family.members) == 1
        assert family.members[0].user_id == user.id
        assert family.members[0].role == 'admin'
        
        # Test: Get User Families
        families = family_service.get_user_families(user.id)
        assert len(families) == 1
        assert families[0].id == family.id
        
        # Test: Add Member
        mom = auth_service.login_or_register_google_user({
            'email': 'mom@example.com', 'sub': '222', 'name': 'Mom', 'picture': ''
        })
        
        member = family_service.add_member(family.id, 'mom@example.com', role='member')
        assert member.user_id == mom.id
        assert member.family_id == family.id
