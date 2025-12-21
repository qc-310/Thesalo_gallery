# 非機能要件定義書 (Non-Functional Requirements Document)

## 1. 性能要件 (Performance Requirements)

- **応答時間 (Response Time)**:
  - 通常のAPIレスポンス: 1秒以内を目標（動的コンテンツ）。
  - 静的コンテンツ（CDN/Nginx経由）: 200ms以内。
  - 重い処理（画像変換等）: 非同期処理とし、UIブロックを避ける。
- **スループット (Throughput)**:
  - 家族利用（数人〜十数人）を想定し、同時接続数 10ユーザー程度で快適に動作すること。
  - GCE e2-micro (2 vCPU, 1GB RAM) の制限内でのベストエフォート。

## 2. 可用性・信頼性 (Availability & Reliability)

- **稼働率**: 個人の思い出管理用のため、商用レベルのSLA（99.9%等）は設定しない。
- **障害対策**:
  - コンテナの自動再起動設定 (`restart: always`)。
  - ログ出力 (Fluentd等なし、ローカルファイルまたはDockerログでの簡易運用)。
- **データ保全**:
  - PostgreSQLのデータボリュームはPersistent Diskに保存。
  - アップロード画像も同様に永続化ディスクに保存。
  - **Backups**: 手動またはCronによる定期的な `pg_dump` とメディア同期（GCS等への退避は別途検討）。

## 3. セキュリティ (Security)

- **通信暗号化**:
  - 全通信 HTTPS化 (Let's Encrypt を使用)。
- **認証・認可**:
  - Google OAuth 2.0 による本人確認。
  - `Family` 単位でのStrictなアクセス制御（他の家族のデータは見えない）。
- **データ保護**:
  - DBパスワード等は環境変数 (`.env`) で管理し、リポジトリに含めない。
  - CSRF対策、XSS対策の実装。

## 4. 保守性・拡張性 (Maintainability & Scalability)

- **コード管理**:
  - GitHubによるバージョン管理。
  - Type Hinting (Python) の活用。
  - **Infrastructure as Code (IaC)**: Terraformを用いてインフラ構成をコード管理し、手動オペレーションによる環境差異を排除する。
- **ドキュメント**:
  - API仕様書、DB設計書の維持管理。
- **デプロイ**:
  - **CI/CD**: GitHub Actionsによる自動テスト・自動デプロイを実装し、リリース作業の効率化とミス防止を図る。
  - Docker Compose コマンド一発で更新可能な構成。
  - 将来的なハイブリッドクラウド化（メディアのみGCS移行など）が可能な設計。

## 5. 運用・監視 (Operations & Monitoring)

- **リソース監視**: GCPコンソールでのCPU/メモリ監視（無料枠内でのアラート設定）。
- **ログ**: アプリケーションエラー時のスタックトレース記録。
