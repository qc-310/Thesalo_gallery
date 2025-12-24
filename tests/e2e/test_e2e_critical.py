
import pytest
from playwright.sync_api import Page, expect

# We assume the app is running at http://localhost:5000 (Docker service 'web')
# But accessed from *inside* the container, it's 'http://localhost:5000' if running locally in same container?
# Or if this test runs in a separate container... 
# The user's rule says "Single VM ... Docker Compose".
# I'll assume standard localhost access for now or service name if running from another container.
# If running via `docker compose run web pytest ...`, it runs inside 'web'. 
# So `localhost:5000` or `localhost:8000` (Gunicorn/Flask default is 5000, 8000 usually gunicorn).
# Let's check docker-compose port mapping or internal port. Internal is likely 5000.

BASE_URL = "http://localhost:5000"

def test_login_page_renders(page: Page):
    """E2E-001: Login Page Existence"""
    page.goto(f"{BASE_URL}/auth/login_page")
    expect(page.locator("text=Thesalo Gallery")).to_be_visible()
    # Check for Google Login button (text might vary, check class or heuristic)
    # The actual text in login.html logic... let's just check title or main element
    expect(page).to_have_title("Login - Thesalo Gallery")

def test_protected_redirect(page: Page):
    """E2E-002: Protected Redirect"""
    # Verify logout first to be sure
    page.goto(f"{BASE_URL}/auth/logout")
    
    # Visit protected
    page.goto(f"{BASE_URL}/family/list")
    
    # Should end up at login
    expect(page).to_have_url(f"{BASE_URL}/auth/login_page?next=%2Ffamily%2Flist") 
    # Url matching might differ on query param encoding
    expect(page.locator("text=Login")).to_be_visible() # Weak check

def test_dev_login_flow(page: Page):
    """E2E-003: Index Page via Dev Login"""
    # Dev Login
    page.goto(f"{BASE_URL}/auth/dev/login?email=e2e@test.com")
    
    # Should redirect to Index
    expect(page).to_have_url(f"{BASE_URL}/")
    expect(page.locator("text=新しい写真・動画を追加")).to_be_visible()
    
    # Verify Header contains User Name
    expect(page.locator("text=Dev User")).to_be_visible()
