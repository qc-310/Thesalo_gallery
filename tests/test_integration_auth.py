
import pytest
from flask import url_for
from app.models.auth import User
from app.extensions import db
import uuid6

def test_integration_auth_login_redirect(client):
    """IT-AUTH-001: Login Redirect"""
    response = client.get('/auth/login')
    # Should redirect to Google's OAuth URL
    assert response.status_code == 302
    assert 'accounts.google.com' in response.headers['Location']

def test_integration_auth_logout(client, app):
    """IT-AUTH-002: Logout"""
    # Simulate logged-in user
    with app.test_request_context():
        # Just verifying the route exists and redirects, 
        # as simulating actual login session in clean integration test 
        # without mocking Authlib internals is tricky.
        # But for integration, we can check basic redirect behavior.
        
        # Access logout
        response = client.get('/auth/logout')
        
        # Should redirect to login (or index which then redirects to login)
        assert response.status_code == 302
        assert 'auth/login' in response.headers['Location'] or 'accounts.google.com' in response.headers['Location']  or response.headers['Location'].endswith('/login')

def test_integration_auth_protected_route(client):
    """IT-AUTH-003: Unauthenticated Access"""
    # Access a protected route (e.g. valid family list)
    response = client.get('/family/list')
    
    # Should be redirected to login
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']
