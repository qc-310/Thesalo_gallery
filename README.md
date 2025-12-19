# Thesalo Gallery

Thesalo Gallery は、Google認証と権限管理(RBAC)を備えた、セキュアな写真・動画共有ギャラリーです。
家族や友人との思い出共有を目的として設計されており、管理者は写真のアップロードや編集ができ、ゲストは閲覧のみが可能です。

## 主な機能

*   **Google認証**: セキュアなログイン機能。
*   **権限管理 (RBAC)**:
    *   **管理者 (Admin)**: 写真のアップロード、編集、削除が可能。
    *   **ゲスト (Guest)**: 閲覧のみ可能（アップロード等は不可）。
*   **マルチアップロード**: 複数の写真・動画を一度にドラッグ＆ドロップでアップロード。
*   **個別コメント**: アップロード時に、写真一枚一枚に対してコメント入力が可能。
*   **EXIF対応**: 写真の撮影日時（EXIF情報）を自動取得し、撮影日順に並び替え。
    *   アプリ起動時に自動で未取得ファイルをスキャン・修正します。
*   **無限スクロール**: 大量の写真もスムーズに閲覧可能。
*   **動画対応**: 動画のアップロードおよびサムネイル自動生成 (ffmpeg使用)。
*   **モバイルフレンドリー**: スマートフォンでの閲覧・操作に最適化されたUI。

## 必要要件

*   Docker / Docker Compose
*   Google Cloud Platform プロジェクト (OAuth 2.0 クライアントIDが必要)

## セットアップ手順

### 1. Google OAuth の設定

1.  Google Cloud Console でプロジェクトを作成。
2.  「APIとサービス」>「認証情報」から **OAuth クライアント ID** を作成。
3.  **承認済みのリダイレクト URI** に以下を設定:
    *   ローカル: `http://localhost:5000/callback`
    *   本番 (Cloudflare Tunnel等): `https://your-domain.com/callback`

### 2. 環境変数の設定 (`docker-compose.yml`)

`docker-compose.yml` を編集し、以下の環境変数を設定してください。

```yaml
environment:
  - FLASK_APP=app.py
  - FLASK_ENV=development
  # Google Cloud Console で取得したIDとシークレット
  - GOOGLE_CLIENT_ID=your_client_id
  - GOOGLE_CLIENT_SECRET=your_client_secret
  
  # ログインを許可するメールアドレス (空欄の場合、Googleアカウントを持つ全員がログイン可能)
  - ALLOWED_EMAILS=
  
  # 管理者権限（アップロード/編集/削除）を与えるメールアドレス (カンマ区切り)
  - ADMIN_EMAILS=admin@example.com,family@example.com
  
  # セッション暗号化キー (本番ではランダムな文字列に変更推奨)
  - FLASK_SECRET_KEY=dev_secret_key_change_in_prod
```

### 3. アプリケーションの起動

```bash
docker-compose up --build -d
```

起動後、`http://localhost:5000` (または設定したドメイン) にアクセスしてください。

## 運用について

*   **データのバックアップ**:
    *   `uploads/`: 写真・動画の実体
    *   `thesalo_gallery.db`: データベース（メタデータ、コメント）
    *   これらを定期的にバックアップしてください。
*   **権限の変更**:
    *   管理者を増やしたい場合は、`docker-compose.yml` の `ADMIN_EMAILS` に追記し、コンテナを再起動してください。

## 技術スタック

*   **Backend**: Python 3.11 (Flask)
*   **Database**: SQLite
*   **Frontend**: HTML5, CSS3 (Grid Layout), Vanilla JS
*   **Auth**: Authlib (OpenID Connect)
*   **Image Processing**: Pillow, pillow-heif (HEIC対応)
*   **Video Processing**: ffmpeg

## ディレクトリ構成

```
.
├── app.py                # メインアプリケーション
├── Dockerfile            # Docker環境定義
├── docker-compose.yml    # コンテナ構成 & 環境変数
├── requirements.txt      # 依存ライブラリ
├── static/               # CSS, JS
├── templates/            # HTMLテンプレート
│   ├── index.html        # ギャラリー (無限スクロール, アップロード)
│   ├── login.html        # ログインページ
│   └── edit.html         # 編集ページ
├── uploads/              # 写真・動画保存先 (Dockerボリューム)
└── thesalo_gallery.db    # データベース
```