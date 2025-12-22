# Unit Test Cases

This document lists the Unit Test cases defined based on the Test Plan and detailed design.

## 1. Auth Module (AuthService)

| ID | Function | Case Description | Input | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-AUTH-001` | `login_or_register_google_user` | **Register New User** | New Google User Info (email, sub) | New `User` record created in DB. ID is not None. | **Implemented** |
| `UT-AUTH-002` | `login_or_register_google_user` | **Login Existing User** | Existing Google User Info (same sub) | Returns existing `User` record. Updates mutable fields (name, pic). | **Implemented** |

## 2. Family Module (FamilyService)

| ID | Function | Case Description | Input | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-FAM-001` | `create_family` | **Create Family** | Valid User, Name="My Family" | New `Family` created. User added as 'admin'. | **Implemented** |
| `UT-FAM-002` | `get_user_families` | **Get User Families** | User ID | Returns list of families the user belongs to. | **Implemented** |
| `UT-FAM-003` | `add_member` | **Add New Member** | Family ID, New User Email | User added to `family_members` table with specified role. | **Implemented** |

## 3. Media Module (MediaService)

| ID | Function | Case Description | Input | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-MEDIA-001` | `upload_media` | **Success Upload (Image)** | Valid `.jpg` file | File saved to `uploads/{fam}/{year}/{month}/`. DB status `processing`. Async task triggered. | **Implemented** (PASS) |
| `UT-MEDIA-002` | `upload_media` | **Invalid Extension** | File with `.txt` extension | Raises `ValueError`. File NOT saved. | **Implemented** (PASS) |
| `UT-MEDIA-003` | `upload_media` | **Duplicate Filename** | File with existing filename | File saved with suffix (e.g., `img_uuid.jpg`). DB record has new filename. | **Implemented** (PASS) |
| `UT-MEDIA-004` | `upload_media` | **MIME Detection** | File with specific signature | Correct `mime_type` stored in DB (e.g. `image/jpeg`). | **Implemented** (PASS) |

## 4. Async Tasks (media_tasks)

| ID | Function | Case Description | Input | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-TASK-001` | `process_media_task` | **Resize Image** | Valid Image Path | Image resized to Max 1920px. EXIF preserved. DB status `ready`. | **Implemented** (PASS) |
| `UT-TASK-002` | `process_media_task` | **Video Thumbnail** | Valid Video Path | Thumbnail generated. DB `thumbnail_path` updated. | **Implemented** (PASS) |
