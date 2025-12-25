# インフラ・デプロイ設計書 (Infrastructure & Deployment Design Document)

## 1. インフラ構成詳細 (Infrastructure Details)

Infrastructure as Code (IaC) ツールとして **Terraform** を使用し、GCPリソースを管理します。

### 1.1 Terraform構成

#### ディレクトリ構造

```text
/terraform
  ├── main.tf           # Cloud Run, IAM, Artifact Registry, Secret Manager定義
  ├── variables.tf      # 変数定義 (workspace prefix等)
  ├── outputs.tf        # Cloud Run URL等の出力
  └── terraform.tfvars  # シークレット値 (Git対象外)
```

#### リソース定義

1. **Project Services**:
    * Cloud Run API
    * Cloud Build API
    * Artifact Registry API
    * Secret Manager API
    * Cloud Tasks API

2. **Secret Manager**:
    * `db-url`: Supabase接続文字列
    * `flask-secret`: アプリケーションSecret Key
    * `google-client-id`, `google-client-secret`: OAuth情報
    * `owner-email`: オーナー権限を持つユーザーのメールアドレス
    * これらをCloud Runの環境変数としてマウント。

3. **Cloud Run**:
    * `google_cloud_run_service`: アプリケーション本体。
    * 環境 (`terraform.workspace`) に応じてリソース名を変更 (`thesalo-web-staging`, `thesalo-web-prod` 等)。
    * **Env Vars**:
        * `STORAGE_BACKEND`: `gcs`
        * `TASK_RUNNER`: `cloud_tasks`

4. **Cloud Tasks**:
    * `google_cloud_tasks_queue`: 非同期処理用キュー。

5. **IAM**:
    * Cloud Run サービスアカウントに必要な権限（Secret Manager Accessor, Cloud Tasks Enqueuer, Storage Admin）を付与。

### 1.2 環境戦略 (Environment Strategy)

Terraform Workspace を使用して環境を分離します。

| Workspace | 用途 | DB | Cloud Run Service |
| :--- | :--- | :--- | :--- |
| **staging** | 統合テスト | Supabase (Staging) | `thesalo-web-staging` |
| **prod** | 本番運用 | Supabase (Prod) | `thesalo-web-prod` |

## 2. デプロイ設計 (Deployment Design)

GitHub Actions を使用し、環境ごとの自動デプロイを実現します。

### 2.1 Workflow: `staging.yml`

1. **Trigger**: `develop` ブランチへのPush。
2. **Build**: Dockerイメージビルド & Artifact RegistryへPush。
3. **Migrate**: Supabase CLI または Migration Container を使用して Staging DB のスキーマ更新。
4. **Deploy**: Terraform Apply (`staging` workspace) で Cloud Run へデプロイ。

### 2.2 Workflow: `production.yml`

1. **Trigger**: `v*` タグのPush。
2. **Build**: Dockerイメージビルド & Artifact RegistryへPush（タグ付き）。
3. **Migrate**: Production DB のスキーマ更新。
4. **Deploy**: Terraform Apply (`prod` workspace) で Cloud Run へデプロイ。

## 3. バックアップ・運用

* **DBバックアップ**: Supabaseの自動バックアップ機能（Point-in-Time Recovery）を利用。
* **メディアバックアップ**: GCSのバージョニング機能を有効化（誤削除対策）。
