# 実装計画: 本番運用に向けたリファクタリング計画

## 1. ギャップ分析 (現状 vs 設計)

| 機能 | 現状 (`app.py`) | 設計目標 (Detailed Design) |
| :--- | :--- | :--- |
| **アーキテクチャ** | 1ファイルのモノリス構成 | モジュラモノリス構成 (Blueprints + Services) |
| **データベース** | SQLite (生SQLクエリ) | PostgreSQL (SQLAlchemy ORM + マイグレーション) |
| **非同期処理** | 同期処理 (Pillow/FFmpeg直列実行) | 非同期分散処理 (Celery + Redis) |
| **認証** | オンメモリ / モック的なセッション | DB永続化 (Users) + Redisセッション管理 |
| **ID体系** | 連番 (Auto-increment Int) | UUID v7 |

## 2. 実装フェーズ (Implementation Phases)

### Phase 1: 環境・インフラ構築 (Step 1-3)

- **目的**: GCE e2-micro で動作するベースコンテナ環境の整備。
- **変更内容**:
  - [ ] アプリケーションのディレクトリ構成 (`app/`) の作成。
  - [ ] `Dockerfile` の最適化 (Python 3.11, マルチステージビルド)。
  - [ ] `docker-compose.yml` の更新 (PostgreSQL, Redis, Celery Worker の追加)。
  - [ ] `requirements.txt` の更新 (SQLAlchemy, Celery 等の追加)。
- **検証**: `docker compose up` で全コンテナがエラーなく起動すること。

### Phase 2: データベース層の実装 (Step 4-6)

- **目的**: ORMを用いた物理データ設計の実装。
- **変更内容**:
  - [ ] DB初期化設定 (`app/models/__init__.py`) の実装。
  - [ ] モデルクラスの実装: `User`, `Family`, `Media`, `Tag`, `Album`。
  - [ ] マイグレーション環境 (Alembic) の初期化と適用。
- **検証**: `flask db upgrade` コマンドで PostgreSQL にテーブルが正しく作成されること。

### Phase 3: コアモジュール (Auth & Family) (Step 7-9)

- **目的**: サービス層を用いた認証・ユーザー管理ロジックの実装。
- **変更内容**:
  - [ ] `AuthService` の実装 (Google OAuthロジック)。
  - [ ] `FamilyService` の実装 (家族グループ管理)。
  - [ ] Blueprint作成: `auth_bp`, `family_bp`。
  - [ ] Flask-Login の `load_user` をDBベースに修正。
- **検証**: Googleログインができ、PostgreSQLの `users` テーブルにレコードが作成されること。

### Phase 4: メディアモジュール & 非同期処理 (Step 10-12)

- **目的**: アプリの核となる写真・動画管理機能の実装。
- **変更内容**:
  - [ ] `MediaService` の実装 (アップロード、参照ロジック)。
  - [ ] `tasks.py` の実装 (Celeryによる画像リサイズ・AI解析)。
  - [ ] Blueprint作成: `media_bp`。
- **検証**: ファイルアップロード時にCeleryタスクがキューイングされ、処理結果 (生成されたサムネイル等) がDBに反映されること。

### Phase 5: フロントエンド結合 & クリーンアップ (Step 13-15)

- **目的**: UIを新APIに結合し、旧コードを完全に排除する。
- **変更内容**:
  - [ ] `templates/` 内の修正 (新しいデータ構造への対応)。
  - [ ] 旧 `app.py` の削除とエンドポイントの完全移行。
- **検証**: タイムライン表示、編集、削除などの操作がブラウザ上で正常に行えること。

## 3. 検証計画 (Verification Plan)

- **自動テスト**: Phase 2以降、`pytest` 環境を整備し、`docker compose run web pytest` で繰り返しテストを実行する。
- **手動確認**: 各フェーズ終了時に `docker compose up` で起動し、ブラウザ (`http://localhost:5000`) から動作確認を行う。

## 4. ブランチ戦略 (Branching Strategy)

**Git-flow** をベースとしつつ、各実装フェーズを大きめのFeatureブランチとして管理します。

| ブランチ名 | 役割 |
| :--- | :--- |
| `main` | 本番用ブランチ (保護)。常にデプロイ可能な状態を維持。 |
| `develop` | 開発用統合ブランチ。CI/CDのテスト対象。 |
| `feature/phase1-infra` | Phase 1 (インフラ構築) 用の作業ブランチ。 |
| `feature/phase2-db` | Phase 2 (DB実装) 用の作業ブランチ。 |
| `feature/phase3-auth` | Phase 3 (認証実装) 用の作業ブランチ。 |
| `feature/phase4-media` | Phase 4 (メディア機能) 用の作業ブランチ。 |
| `feature/phase5-frontend` | Phase 5 (UI移行) 用の作業ブランチ。 |

**ワークフロー**:

1. `develop` から `feature/phaseX-xxx` を作成。
2. 実装作業を行い、細かくCommit。
3. フェーズ完了後、`develop` へPull Requestを作成・マージ。
