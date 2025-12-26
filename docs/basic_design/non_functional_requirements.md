# 非機能要件定義書 (Non-Functional Requirements Document)

## 1. 性能要件 (Performance Requirements)

- **応答時間 (Response Time)**:
  - 通常のAPIレスポンス: 1秒以内を目標（Cloud Run Cold Start時を除く）。
  - Cold Start許容: 初回アクセス時に数秒〜10秒程度の遅延が発生することを許容する（コスト優先）。
  - 重い処理（画像変換等）: Cloud Tasksによる非同期処理とし、Webレスポンスは即時（Accept 202）を返す。
- **スケーラビリティ (Scalability)**:
  - **Scale to Zero**: アイドル時はインスタンス数0までスケールダウンし、コストを最小化する。
  - **Auto Scaling**: トラフィック増加時に自動的にインスタンスを追加する（最大インスタンス数はコスト保護のため低めに設定: max 5-10）。

## 2. 可用性・信頼性 (Availability & Reliability)

- **稼働率**: 個人の思い出管理用のため、商用レベルのSLA（99.9%等）は設定しない。Cloud Run / Supabase の SLA に準拠。
- **データ保全**:
  - **DB**: Supabase (PostgreSQL) のマネージドバックアップを利用。
  - **Storage**: GCS (Google Cloud Storage) の高い耐久性 (99.999999999%) に依存。バージョニングを有効化し、誤削除を防ぐ。

## 3. セキュリティ (Security)

- **通信暗号化**:
  - Cloud Run が標準提供する HTTPS エンドポイントを使用。
- **認証・認可**:
  - Google OAuth 2.0 による本人確認。
  - `Family` 単位でのStrictなアクセス制御（PostgreSQL RLS - Row Level Security も併用検討）。
- **データ保護**:
  - DB接続情報、APIキー等は Secret Manager で厳重に管理し、ソースコードには一切含めない。
  - コンテナはステートレスであり、再起動でメモリ上のデータは消去されるため、機密情報の残留リスクが低い。

## 4. 保守性・拡張性 (Maintainability & Scalability)

- **Configuration**:
  - 環境変数 (`os.environ`) と Secret Manager で構成を分離。
  - Terraformにより、Staging/Production 環境を同一構成で再現可能にする。
- **CI/CD**:
  - GitHub Actions による自動テスト・自動デプロイ。
  - `develop` ブランチへのPushでStagingへ、タグPushでProductionへデプロイ。

## 5. 運用・監視 (Operations & Monitoring)

- **ログ**: Cloud Logging に集約。構造化ログを出力し、フィルタリングを容易にする。
- **エラー通知**: アプリケーションエラー時にログレベル `ERROR` を出力し、Cloud Loggingのアラート機能で検知（要設定）。
