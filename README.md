# Thesalo Gallery v2.0.0

Thesalo Gallery は、Google認証と権限管理(RBAC)を備えた、セキュアな写真・動画共有ギャラリーです。
家族や友人との思い出共有を目的として設計されており、役割（Owner, Family, Guest）に応じた柔軟な権限管理が可能です。

## 主な機能

* **Google認証**: セキュアなログイン機能 (OpenID Connect)。
* **権限管理 (RBAC)**:
  * **Owner (管理者)**: 全権限。ユーザー管理（権限変更）、削除などが可能。
  * **Family (家族)**: 写真・動画のアップロード、編集、タグ付けが可能。
  * **Guest (ゲスト)**: 閲覧および「お気に入り (Like)」のみ可能。
* **ペット管理**: ペットのプロフィール登録、自己紹介、アイコン設定。
* **マルチメディア対応**:
  * **写真**: EXIF情報自動取得、撮影日順ソート、HEIC対応、クロッピング機能。
  * **動画**: サムネイル自動生成 (ffmpeg)、ブラウザでの再生に対応。
* **非同期処理**: Celery + Redis による画像の最適化・変換処理のバックグラウンド実行。
* **お気に入り**: 写真・動画へのお気に入り登録とフィルタリング。
* **モバイル最適化**: スマートフォンでの操作性を重視したレスポンシブデザイン。

## 技術スタック

* **Backend**: Python 3.11 (Flask)
* **Database**: PostgreSQL 15
* **Queue/Cache**: Redis 7
* **Worker**: Celery (非同期タスク)
* **Frontend**: HTML5, CSS3 (Grid/Masonry), Vanilla JS
* **Auth**: Authlib (Google OAuth 2.0)
* **Infrastructure**: Docker, Docker Compose

## 必要要件

* Docker / Docker Compose
* Google Cloud Platform プロジェクト (OAuth 2.0 クライアントIDが必要)

## セットアップ手順

### 1. Google OAuth の設定

1. Google Cloud Console でプロジェクトを作成。
2. 「APIとサービス」>「認証情報」から **OAuth クライアント ID** を作成。
3. **承認済みのリダイレクト URI** に以下を設定:
    * ローカル: `http://localhost:5000/auth/callback`
    * 本番: `https://your-domain.com/auth/callback`

### 2. 環境変数の設定 (`.env`)

ルート直下に `.env` ファイルを作成し、以下の環境変数を設定してください。

```bash
# Flask Config
FLASK_APP=app:create_app
FLASK_DEBUG=1
FLASK_SECRET_KEY=change_this_to_random_secret_string

# Database & Cache
DATABASE_URL=postgresql://user:password@db:5432/thesalo_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Owner Configuration (Initial Setup)
# 最初にこのメールアドレスでログインしたユーザーが自動的に Owner 権限を取得します
OWNER_EMAIL=your_email@example.com

# Upload Settings
MAX_IMAGE_SIZE=1920
```

### 3. アプリケーションの起動

```bash
docker compose up --build -d
```

起動後、`http://localhost:5000` にアクセスしてください。

### 4. ユーザー権限の設定

1. `.env` の `OWNER_EMAIL` に設定したアカウントでログインします（自動的にOwnerになります）。
2. アプリ内の「設定」→「ユーザー管理」にアクセスします。
3. 他のユーザー（家族）がログインした後、リストから「家族にする」ボタンを押して権限を付与してください。
   * 新規ユーザーはデフォルトで **Guest (閲覧のみ)** として登録されます。

## ディレクトリ構成

```text
.
├── app/                  # アプリケーションコード
│   ├── blueprints/       # 機能モジュール (auth, core, media, pets)
│   ├── models/           # データベースモデル
│   ├── services/         # ビジネスロジック
│   ├── static/           # CSS, JS, Images
│   └── templates/        # HTMLテンプレート
├── scripts/              # ユーティリティスクリプト
├── uploads/              # メディア保存先 (Dockerボリューム)
├── migrations/           # DBマイグレーションファイル
├── docker-compose.yml    # コンテナ構成
└── Dockerfile            # Dockerイメージ定義
```

## 運用について

* **バックアップ**:
  * `uploads/` ディレクトリ（写真・動画の実体）
  * `postgres_data` ボリューム（データベース）
* **ログ確認**:
  * `docker compose logs -f` でアプリとワーカーのログを確認できます。
