# Thesalo Gallery v3.0.0

Thesalo Gallery は、Google認証と権限管理(RBAC)を備えた、セキュアな写真・動画共有ギャラリーです。
家族や友人との思い出共有を目的として設計されており、Cloud Run + Supabase によるモダンな構成で動作します。

## 主な機能

* **Google認証**: セキュアなログイン機能 (OpenID Connect)。
* **権限管理 (RBAC)**:
  * **Owner (管理者)**: 全権限。ユーザー管理（権限変更）、削除などが可能。
  * **Family (家族)**: 写真・動画のアップロード、編集、タグ付けが可能。
  * **Guest (ゲスト)**: 閲覧および「お気に入り (Like)」のみ可能。
* **ペット管理**: ペットのプロフィール登録、自己紹介、アイコン設定。
* **マルチメディア対応**:
  * **写真**: EXIF情報自動取得、撮影日順ソート、HEIC対応。
  * **動画**: サムネイル自動生成、ブラウザでの再生に対応。
* **ハイブリッドアーキテクチャ**:
  * **Local**: Local File System + 同期処理 (Sync) で手軽に開発。
  * **Prod**: Google Cloud Storage + Cloud Tasks でスケーラブルに稼働。
* **お気に入り**: 写真・動画へのお気に入り登録とフィルタリング。
* **モバイル最適化**: スマートフォンでの操作性を重視したレスポンシブデザイン。

## 技術スタック

* **Backend**: Python 3.11 (Flask 3.x)
* **Database**: PostgreSQL 15 (Supabase / Local)
* **Storage**: Google Cloud Storage / Local File System
* **Async Tasks**: Google Cloud Tasks (Prod) / Sync execution (Local)
* **Frontend**: HTML5, CSS3 (Grid/Masonry), Vanilla JS
* **Auth**: Authlib (Google OAuth 2.0)
* **Infrastructure**: Docker, Terraform, Cloud Run

## 必要要件

* Docker / Docker Compose
* Google Cloud Platform プロジェクト (OAuth 2.0 クライアントIDが必要)

## セットアップ手順 (ローカル開発)

### 1. Google OAuth の設定

1. Google Cloud Console でプロジェクトを作成。
2. 「APIとサービス」>「認証情報」から **OAuth クライアント ID** を作成。
3. **承認済みのリダイレクト URI** に以下を設定:
    * ローカル: `http://localhost:5000/auth/callback`

### 2. 環境変数の設定 (`.env`)

ルート直下に `.env` ファイルを作成し、以下の環境変数を設定してください（`.env.example` 参照）。

```bash
# Flask Config
FLASK_APP=app:create_app
FLASK_DEBUG=1
FLASK_SECRET_KEY=change_this_to_random_secret_string

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Owner Configuration
OWNER_EMAIL=your_email@example.com

# Local Dev Settings
STORAGE_BACKEND=local
TASK_RUNNER=sync
BYPASS_AUTH=true
# DATABASE_URL は docker-compose.yml のデフォルト値が使用されるため設定不要（カスタマイズ可）
```

### 3. アプリケーションの起動

```bash
docker compose up --build -d
```

起動後、`http://localhost:5000` にアクセスしてください。
開発モード (`BYPASS_AUTH=true`) の場合、ログイン画面に表示される「Dev Owner Login」ボタンで即座に管理者としてログインできます。

## デプロイ (Production)

本番環境へのデプロイは **Terraform** と **GitHub Actions** によって管理されています。

1. **Infrastructure**: `terraform/` ディレクトリ内のコードで Cloud Run, Supabase, GCS 等を構築します。
2. **CI/CD**: GitHub Actions により、タグ (`v*`) のプッシュをトリガーとして本番デプロイが行われます。

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
├── uploads/              # メディア保存先 (Local Dev用)
├── migrations/           # DBマイグレーションファイル
├── terraform/            # インフラ定義 (GCP)
├── docker-compose.yml    # ローカル開発用コンテナ構築
└── Dockerfile            # 本番/開発共通コンテナ定義
```
