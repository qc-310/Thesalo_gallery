# インフラ・デプロイ設計書 (Infrastructure & Deployment Design Document)

## 1. インフラ構成詳細 (Infrastructure Details)

### 1.1 Terraform構成

Infrastructure as Code (IaC) ツールとして **Terraform** を使用し、GCPリソースを管理します。

#### ディレクトリ構造

```text
/terraform
  ├── main.tf           # メインのリソース定義
  ├── variables.tf      # 変数定義
  ├── outputs.tf        # 出力定義
  ├── terraform.tfvars  # 環境依存の変数値 (Git対象外)
  └── modules/          # (必要に応じてモジュール化)
```

#### リソース定義

1. **Network**:
    * `google_compute_network` (VPC): `thesalo-vpc`
    * `google_compute_subnetwork`: `thesalo-subnet` (Region: `us-west1` 等、Free Tier対象リージョン)
    * `google_compute_firewall`:
        * `allow-http-https`: Ingress 80, 443 (Tag: `http-server`)
        * `allow-ssh`: Ingress 22 (Source: Admin IP or IAP)
2. **Compute Engine**:
    * `google_compute_instance`:
        * Machine Type: `e2-micro`
        * Zone: `us-west1-b` (例)
        * OS Image: `ubuntu-os-cloud/ubuntu-2204-lts`
        * Disk: Standard Persistent Disk 30GB
        * Tags: `http-server`, `https-server`
3. **Static IP**:
    * `google_compute_address`: `thesalo-static-ip` (インスタンスに紐付け)

### 1.2 プロビジョニング (Provisioning)

インスタンス起動時の初期設定には **cloud-init** (`user-data`) を使用します。

* **処理内容**:
    1. Docker, Docker Compose のインストール。
    2. 作業用ユーザー (`appuser`) の作成とDockerグループへの追加。
    3. アプリケーションディレクトリ (`/app`) の作成と権限設定。
    4. スワップ領域の確保 (e2-microのメモリ不足対策として 2GB 程度のSwapファイルを作成)。

## 2. デプロイ設計 (Deployment Design)

### 2.1 デプロイメントパイプライン

GitHub Actions を使用し、コードの変更を自動的に本番環境へ反映します。

#### Workflow: `deploy.yml`

1. **Trigger**: `main` ブランチへのPush。
2. **Build Job**:
    * Dockerイメージのビルド (`app`, `nginx`)。
    * Google Artifact Registry (GAR) または Docker Hub へのPush。
3. **Deploy Job**:
    * `gcloud` SDK セットアップ (Service Account認証)。
    * Terraform Apply (インフラ変更がある場合)。
    * SSH経由でGCEインスタンスに接続。
    * 最新の `docker-compose.yml` を転送。
    * `docker compose pull && docker compose up -d` を実行。
    * 古いイメージの削除 (`docker image prune`).

### 2.2 秘密情報管理 (Secrets Management)

* **GitHub Secrets**:
  * `GCP_SA_KEY`: Terraform/GCE操作用サービスアカウントキー。
  * `SSH_PRIVATE_KEY`: インスタンス接続用。
  * `ENV_FILE`: 本番用 `.env` ファイルの中身。
* **GCE Metadata / .env**:
  * デプロイ時にGitHub Secretsから `.env` ファイルを生成し、サーバー上の所定位置に配置する。

## 3. バックアップ・運用

* **DBバックアップ**: Cronジョブで `pg_dump` を実行し、GCS (Google Cloud Storage) へ転送（ライフサイクル設定で古いものを削除）。
* **メディアバックアップ**: Persistent Diskのスナップショットスケジュールを設定（日次/週次）。
