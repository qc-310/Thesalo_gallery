# セキュリティ設計書 (Security Design Document)

## 1. 認証と認可 (Authentication & Authorization)

### 1.1 認証 (Authentication)

- **基盤**: Google OAuth 2.0 (OpenID Connect)
- **セッション管理**:
  - サーバーサイド: Redisにセッション情報を保存。
  - クライアントサイド: HttpOnly, Secureクッキー (Session IDのみ)。
  - 有効期限: 7日間 (リフレッシュトークン利用)。

### 1.2 認可 (Authorization)

- **モデル**: 家族単位のアクセス制御 (Family-Based Access Control)。
- **制御ロジック**:
  - 全APIリクエストにおいて `current_user` がリクエスト対象リソースの `family_id` に所属しているかを **Service Layer** で必ず検証する（`@login_required` + `PermissionCheck`）。
  - 管理者機能（システム設定等）は `role='admin'` 保持者のみ実行可能。

## 2. アプリケーションセキュリティ (Application Security)

### 2.1 Web脆弱性対策

- **CSRF (Cross-Site Request Forgery)**:
  - Flask-WTF を使用し、全ての `POST`, `PUT`, `DELETE` リクエストでCSRFトークンを検証。
- **XSS (Cross-Site Scripting)**:
  - Jinja2 テンプレートエンジンのオートエスケープ機能を有効化。
  - ユーザー入力値のHTMLタグ除去（サニタイズ）。
- **SQL Injection**:
  - SQLAlchemy ORM を全面的に使用し、プリペアドステートメントによるクエリ発行を強制。生SQLは原則禁止。

### 2.2 ファイルアップロード

- **コンテンツ検証**: 拡張子だけでなく、バイナリヘッダー（Magic Number）による実際のファイル形式チェック。
- **実行防止**: アップロードディレクトリ (`/uploads`) からのスクリプト実行権限を剥奪（Nginx設定）。
- **サイズ制限**: アプリケーションおよびWebサーバーでのサイズ制限 (1GB)。

## 3. ネットワーク・インフラセキュリティ (Network & Infra Security)

### 3.1 通信の暗号化

- **HTTPS**: Let's Encrypt を使用し、全ての通信をSSL/TLS化。HTTPアクセスはHTTPSへリダイレクト。
- **HSTS**: HTTP Strict Transport Security ヘッダーを付与。

### 3.2 ネットワーク制限

- **Firewall (GCP Firewall Rules)**:
  - `0.0.0.0/0`: Port 80, 443 のみ許可。
  - SSH (22): 特定IPアドレス、または GCP IAP (Identity-Aware Proxy) 経由のみ許可（推奨）。
  - DB/Redisポート (5432, 6379): 外部公開せず、Dockerネットワーク内でのみ通信。

## 4. データ保護 (Data Protection)

### 4.1 機密情報の管理

- **環境変数**: APIキー、DBパスワード、Secret Key等は `.env` ファイル (GCE上ではメタデータ等) で管理し、コードリポジトリにはコミットしない。

### 4.2 ストレージの暗号化

- **GCE Persistent Disk**: Google Cloudの標準機能により、自動的に暗号化 (Encryption at Rest) される。
