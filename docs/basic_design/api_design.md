# インターフェース設計書 (API Design Document)

## 1. 設計方針 (Design Principles)

- **RESTful API**: リソース指向のURL設計。
- **Response Format**: JSON。
- **Authentication**: Bearer Token (Session Cookie も併用するが、API文脈ではステートレスを意識)。
- **Status Codes**: 適切なHTTPステータスコードの使用 (200, 201, 400, 401, 403, 404, 500)。

## 2. エンドポイント一覧 (Endpoints)

### 2.1 認証 (Authentication)

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/auth/login` | Googleログイン開始 |
| `GET` | `/auth/callback` | Googleコールバック |
| `GET` | `/auth/logout` | ログアウト |
| `GET` | `/api/v1/me` | 自身のユーザー情報取得 |

### 2.2 メディア (Media)

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/media` | メディア一覧取得 (フィルター, ページング) |
| `POST` | `/api/v1/media` | 新規メディアアップロード (Multipart) |
| `GET` | `/api/v1/media/{id}` | メディア詳細取得 |
| `PATCH` | `/api/v1/media/{id}` | メディアメタデータ更新 (コメント, タグ) |
| `DELETE` | `/api/v1/media/{id}` | メディア削除 |
| `POST` | `/api/v1/media/{id}/favorite` | お気に入りトグル |

### 2.3 家族・ペット (Families & Pets)

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/families/current` | 現在の家族情報・メンバー取得 |
| `POST` | `/api/v1/families/invite` | 招待リンク生成 (Admin only) |
| `GET` | `/api/v1/pets` | ペット一覧取得 |
| `POST` | `/api/v1/pets` | ペット新規登録 |
| `PATCH` | `/api/v1/pets/{id}` | ペット情報更新 |

### 2.4 その他 (Misc)

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/tags` | 利用可能なタグ一覧取得 |
| `GET` | `/api/v1/system/storage` | ストレージ使用量取得 |

## 3. インターフェース詳細 (Interface Details)

### 3.1 メディア一覧 (`GET /api/v1/media`)

- **Query Parameters**:
  - `page`: default 1
  - `limit`: default 24
  - `pet_id`: (optional)
  - `type`: `image` | `video`
  - `sort`: `taken_at_desc` (default) | `created_at_desc`
- **Response (200)**:

```json
{
  "data": [
    {
      "id": "uuid",
      "type": "image",
      "thumbnail_url": "https://...",
      "original_url": "https://...",
      "taken_at": "2023-10-01T12:00:00Z",
      "is_favorite": false,
      "tags": [{"id": "...", "name": "散歩"}]
    }
  ],
  "meta": {
    "current_page": 1,
    "last_page": 10,
    "total": 240
  }
}
```

### 3.2 メディアアップロード (`POST /api/v1/media`)

- **Content-Type**: `multipart/form-data`
- **Body**:
  - `files[]`: Binary (Multiple files supported)
  - `comments[]`: String (Optional, mapped by index)
- **Response (202 Accepted)**:
  - アップロードを受け付け、バックグラウンド処理を開始したことを示す。

```json
{
  "message": "Upload accepted. Processing started.",
  "job_ids": ["job_uuid_1", "job_uuid_2"]
}
```

### 3.3 エラーレスポンス (Error Response)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File size exceeds the limit of 1GB."
  }
}
```
