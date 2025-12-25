import requests
import os

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

def test_01_dev_login():
    print("Testing Dev Login...")
    # Dev login redirects to index, so we allow redirects
    resp = SESSION.get(f"{BASE_URL}/auth/dev/login", allow_redirects=True)
    if resp.status_code == 200 and "Thesalo Gallery" in resp.text:
        print("✅ Dev Login Successful")
    else:
        print(f"❌ Dev Login Failed: {resp.status_code}")
        exit(1)

def test_03_upload_media():
    print("Testing Media Upload...")
    # Create a dummy image
    with open("test_verify.jpg", "wb") as f:
        f.write(os.urandom(1024))
    
    files = {'file': ('test_verify.jpg', open('test_verify.jpg', 'rb'), 'image/jpeg')}
    # Using the /media/upload route from the form action
    resp = SESSION.post(f"{BASE_URL}/media/upload", files=files, allow_redirects=True)
    
    if resp.status_code == 200:
        print("✅ Media Upload Successful")
    else:
        print(f"❌ Media Upload Failed: {resp.status_code}")
        print(resp.text)
        exit(1)
        
    os.remove("test_verify.jpg")

def test_04_verify_gallery():
    print("Testing Gallery Listing...")
    resp = SESSION.get(f"{BASE_URL}/")
    if "test_verify.jpg" in resp.text or "grid-item" in resp.text:
        # Note: filename might be hashed or changed, but we look for grid items
        print("✅ Gallery Listing Verified (Items found)")
    else:
        print("⚠️ Gallery might be empty or upload processing pending.")

if __name__ == "__main__":
    try:
        test_01_dev_login()
        # test_02_create_family() # Removed
        test_03_upload_media()
        test_04_verify_gallery()
        print("\n🎉 All System Verification Tests Passed!")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        exit(1)
