# テスト仕様書 (Test Specification Document)

## 1. テスト戦略 (Testing Strategy)

### 1.1 テストピラミッド

本プロジェクトでは、実行速度と保守性を重視し、以下の比率でテストを実装します。

1. **Unit Tests (単体テスト)**: ~70%
    * 対象: Service Layer, Model, Utility functions.
    * 特徴: DBや外部APIをMock化し、ロジック単体を高速に検証。
2. **Integration Tests (結合テスト)**: ~30%
    * 対象: API Endpoints (Flask Views).
    * 特徴: テスト用DBを使用し、RequestからResponseまでの一連のフロー（DB書き込み含む）を検証。Celeryタスクは同期実行 (`CELERY_TASK_ALWAYS_EAGER`) またはMockで検証。
3. **E2E Tests**: (今回はスコープ外・手動実施)

### 1.2 テストツール

- **Framework**: `pytest`
* **Runner**: `pytest`
* **Plugins**:
  * `pytest-cov`: カバレッジ計測 (目標: Logic層 80%以上)。
  * `pytest-flask`: Flaskアプリのテスティングクライアント。
  * `factory-boy`: テストデータ（Fixture）の生成。

## 2. テスト範囲と観点 (Test Scope & Perspectives)

### 2.1 認証モジュール (Auth)

- **Unit**:
  * `AuthService.login_with_google`: ID Tokenの検証ロジック（Mock）、ユーザー作成、セッション生成が正しく行われるか。
* **Integration**:
  * `GET /auth/login`: リダイレクトURLが正しいか。
  * `GET /api/v1/me`: 未ログイン状態で401、ログイン状態で正しいJSONが返るか。

### 2.2 メディアモジュール (Media)

- **Unit**:
  * `MediaService.upload_media`: ファイルサイズバリデーション、DBへのレコード挿入、Celeryタスクの呼び出し確認。
* **Integration**:
  * `POST /api/v1/media`:
    * 正常系: 202レスポンス、DBに `processing` ステータスで保存。
    * 異常系: 不正な拡張子、サイズ超過で400エラー。
  * `GET /api/v1/media`: フィルタリング（`pet_id`, `type`）が正しく機能するか。

### 2.3 非同期タスク (Async Tasks)

- **Unit**:
  * `process_media_task`:
    * 画像処理ライブラリ (Pillow) をMock化し、リサイズロジックが呼ばれるか。
    * 処理成功時にDBステータスが `ready` に更新されるか。
    * 例外発生時にリトライ、または `error` ステータスへ遷移するか。

### 2.4 権限管理 (Permissions)

- **Integration**:
  * 他の家族 (`family_id`) のリソースにアクセスしようとした際、`403 Forbidden` が返却されること。
  * 招待されていない家族のAPIを叩けないこと。

## 3. テストデータ管理

- `tests/conftest.py` に共有Fixtureを定義。
* `Factory` クラスを用いて、`User`, `Family`, `Media` 等のテストデータを動的に生成し、テスト終了後にロールバック（またはDBコンテナのリセット）を行う。

## 4. 自動化実装 (Automation Implementation)

### 4.1 ローカル実行 (Local Execution)

開発者が手元でテストを実行する手順。Docker環境内で実行することで、本番との環境差異をなくす。

```bash
# 全テスト実行
docker compose run --rm web pytest

# 特定のテストファイルのみ実行
docker compose run --rm web pytest tests/test_auth.py

# カバレッジレポート出力
docker compose run --rm web pytest --cov=app tests/
```

### 4.2 CIパイプライン (GitHub Actions)

Pull Request作成時と `main` ブランチへのマージ時に自動実行するワークフロー定義 (`.github/workflows/test.yml`)。

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-flask pytest-cov
      - name: Run Tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        run: pytest --cov=app tests/
```

## 5. テスト完了条件 (Done Definition)

- 全てのUnit/IntegrationテストがPassすること。
* Logic層のカバレッジが80%を超えていること。
