# 変更履歴 (Changelog)

このプロジェクトのすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/lang/ja/) に準拠しています。

## [3.0.0] - 2025-12-25

### ⚠️ 破壊的変更 (Breaking Changes)

- **Family機能の廃止**: アプリケーションの簡素化のため、「家族 (Family)」機能を完全に削除しました。
  - `Families`, `FamilyMembers` テーブルを削除し、`PetProfiles` と `Media` の関連付けを刷新しました。
  - ユーザーロールを `Owner`, `Family`, `Guest` の3種類に整理し、`Owner` が全ての管理権限を持つ形に変更しました。

### 追加 (Added)

- **開発効率化 (Local Dev)**:
  - **ハイブリッドストレージ**: ローカル開発時はファイルシステム (`uploads/`)、本番は GCS を自動で切り替える機能を追加しました。
  - **同期タスクランナー**: ローカル開発時に Cloud Tasks を経由せず、即座に画像処理を実行するモードを追加しました。
  - **Dev Login**: 開発時にワンクリックで管理者としてログインできるバイパス機能を追加しました。
- **インフラ (Infrastructure)**:
  - **Terraform導入**: GCPリソース (Cloud Run, GCS, Secret Manager, Cloud Tasks) の構成管理をコード化しました。
  - **マルチ環境対応**: `staging` と `prod` の2環境を完全に分離し、Terraform Workspaceを用いずにディレクトリベースで分離しました。
  - **Cloudflare連携**: DNSレコードとProxy設定をTerraformで管理するようにしました。
  - **コスト最適化**: Cloud Runのインスタンス数制限 (Min 0/Max 1)、予算アラート、Artifact Registryの自動掃除ポリシーを適用しました。
  - **Keyless CI/CD**: Workload Identity Federation (OIDC) を導入し、Service Account Key jsonを廃止しました。
  - **Secret Manager対応**: データベースURLやOAuthシークレットなどの機密情報を Secret Manager から安全に注入する仕組みを構築しました。
- **CI/CD**:
  - **Feature Flow**: PR作成時にCodeQL, Flake8, pytestを実行するワークフローを追加。
  - **Staging Pipeline**: `develop` ブランチへのプッシュでStaging環境へ自動デプロイ。
  - **Production Pipeline**: `v*` タグのプッシュでProduction環境へ自動デプロイ。
- **ドキュメント**:
  - データ設計書 (`data_design.md`)、処理ロジック (`processing_logic.md`)、システム構成図 (`system_architecture.md`) を現在のアーキテクチャに合わせて全面改訂しました。

### 変更 (Changed)

- **コードベース最適化**: 未使用のスクリプト、テストコード、テンプレートを削除し、ディレクトリ構成を整理しました。
- **Docker構成**: プロダクションビルド用に `.dockerignore` を最適化し、イメージサイズとセキュリティを向上させました。

## [1.1.1] - 2025-12-20

### 開発環境 (Dev)

- **DevContainer**: VS Code DevContainerに対応しました。`Reopen in Container` で開発環境を即座に構築できます。
- **Dockerfile**: ビルド依存関係 (`wget`) を修正しました。

## [1.1.0] - 2025-12-19

### 追加 (Added)

- **画像の最適化**: アップロードされた画像を自動的に長辺最大1920pxにリサイズし、JPEG形式 (画質85) に圧縮するようにしました。これによりサーバー容量を節約し、表示速度を向上させます。
- **HEIC変換**: iPhone等で撮影された `.heic` 形式の画像を、ブラウザ互換性の高い `.jpg` に自動変換して保存するようにしました。
- **ドキュメント**: 更新履歴を管理するための `CHANGELOG.md` を追加しました。

## [1.0.0] - 2025-12-19

### 追加 (Added)

- **Google認証**: Google OAuth 2.0 (OpenID Connect) を使用したセキュアなログイン機能を実装しました。
- **権限管理 (RBAC)**:
  - **管理者 (Admin)**: `ADMIN_EMAILS` で指定されたユーザーのみ、写真のアップロード・編集・削除が可能。
  - **ゲスト (Guest)**: その他のログインユーザーは閲覧のみ可能。
- **マルチアップロード**: 複数のファイルをドラッグ＆ドロップで一度にアップロード可能にしました。
- **個別コメント**: アップロード前のプレビュー画面で、写真ごとにコメントを入力できるようにしました。
- **EXIFソート機能**: 写真のEXIFデータ (`DateTimeOriginal`) を抽出し、撮影日時順に並び替える機能を実装しました。
- **自動スキャン**: サーバー起動時に、日時情報が未取得の既存写真を自動スキャンして修復する機能を追加しました。
- **無限スクロール**: 写真枚数が増えても動作が重くならないよう、ギャラリーページに無限スクロールを導入しました。
- **動画対応**: 動画ファイル (`.mp4`, `.mov` 等) のアップロードと、サムネイルの自動生成に対応しました。

### 変更 (Changed)

- **UI/UX**: Masonryレイアウト（タイル状配置）とライトボックス表示を採用し、モダンでレスポンシブなデザインに刷新しました。
- **技術スタック**: Python 3.11 ベースへアップデートし、Flask 2.x 構成にリファクタリングしました。
