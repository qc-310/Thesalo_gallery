# エラーハンドリング・ログ設計書 (Error Handling & Log Design Document)

## 1. エラーハンドリング方針 (Error Handling Policy)

### 1.1 基本方針

- **統一されたエラーレスポンス**: APIのエラーは常に決まったJSONフォーマットで返却し、クライアント側でのハンドリングを統一する。
- **独自例外クラス**: アプリケーション固有のエラーはカスタム例外クラス (`AppException` 継承) を定義して送出する。
- **グローバルハンドラ**: Flaskの `errorhandler` を用いて、予期せぬ例外を含む全てのエラーを捕捉し、適切なHTTPステータスとログ出力を行う。

### 1.2 エラーレスポンス形式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "指定されたメディアは見つかりませんでした。",
    "details": null
  }
}
```

### 1.3 HTTPステータスコード定義

| Code | Meaning | Description |
| :--- | :--- | :--- |
| `400` | Bad Request | 入力値不正、バリデーションエラー。 |
| `401` | Unauthorized | 未認証、セッション切れ。 |
| `403` | Forbidden | アクセス権限なし（別家族のデータへのアクセス等）。 |
| `404` | Not Found | リソース不在。 |
| `429` | Too Many Requests | レートリミット超過。 |
| `500` | Internal Server Error | サーバー内部エラー（バグ、DB接続断など）。 |

### 1.4 例外クラス階層

- `AppException` (Base)
  - `ValidationException` (400)
  - `AuthenticationException` (401)
  - `PermissionException` (403)
  - `ResourceNotFoundException` (404)
  - `BusinessLogicException` (400/409 - 業務ルール違反)

### 1.5 非同期タスクのエラーハンドリング (Async Task Error Handling)

Celery Workerでのバックグラウンド処理におけるエラー対応。

- **Retry (リトライ)**:
  - 一時的な障害（ネットワーク瞬断など）の場合、最大3回まで指数バックオフ (Exponential Backoff) でリトライを行う。
- **Final Failure (最終的な失敗)**:
  - リトライ上限に達した場合、またはリトライ不可能なエラー（ファイル破損など）の場合。
  - 該当 `media` レコードの `status` を `error` に更新する。
  - 管理者通知レベル (`ERROR`) でログを出力する。

## 2. ログ設計方針 (Log Design Policy)

### 2.1 基本方針

- **構造化ログ (Structured Logging)**: JSON形式で出力し、Cloud Logging等での検索・分析を容易にする。
- **標準出力**: コンテナ環境（Docker/GCE）のため、ログは全て `stdout` / `stderr` に出力する。
- **コンテキスト情報**: リクエストID、ユーザーID、パスなどを付与し、トレーサビリティを確保する。

### 2.2 ログレベル基準

| Level | Description | Target |
| :--- | :--- | :--- |
| `ERROR` | システムの動作継続に支障がある、またはユーザーへのサービス提供に失敗した異常。 | 例外発生、DB接続失敗、外部APIタイムアウト |
| `WARNING` | 正常ではないが、サービス継続は可能。要確認。 | 予期しない入力データ、非推奨APIの使用 |
| `INFO` | 正常動作の記録。主要なイベント。 | ログイン成功、メディアアップロード完了、バッチ処理開始/終了 |
| `DEBUG` | 開発・デバッグ用詳細情報。 | SQLクエリ発行、変数のダンプ（本番では原則OFF） |

### 2.3 ログフォーマット (JSON)

```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "level": "INFO",
  "request_id": "req-12345",
  "user_id": "user-uuid",
  "path": "/api/v1/media",
  "method": "POST",
  "message": "Media upload completed successfully.",
  "extra": {
    "media_id": "media-uuid",
    "file_size": 102400
  }
}
```

### 2.4 ログ確認方法 (Log Inspection)

本環境はDockerコンテナで構成されているため、標準出力されたログはDockerエンジンによって管理されます。

1. **リアルタイム確認**:

    ```bash
    # 全コンテナのログを流し見
    docker compose logs -f
    # 特定サービス（例: Webアプリ）のみ
    docker compose logs -f web
    ```

2. **過去ログの検索**:

    ```bash
    # 直近100行を表示
    docker compose logs --tail 100 web
    # grepでエラーのみ抽出
    docker compose logs web | grep "ERROR"
    ```

### 2.5 GCP Cloud Logging (参考・オプション)

GCPコンソール上でログを確認することも可能ですが、本システムの構成（e2-micro 1台）では推奨しません。

- **機能**: **Cloud Logging** (旧 Stackdriver) にログを転送し、ブラウザで検索・閲覧が可能。
- **コスト**: 毎月 **50GiB** まで無料（それを超えると有料）。本規模では実質無料。
- **注意点 (重要)**:
  - ログ転送には VM 内に **Ops Agent** のインストールが必要です。
  - Ops Agent はメモリを消費するため、**e2-micro (メモリ1GB)** の環境ではアプリケーションの動作を圧迫する（OOM Killのリスクが高まる）可能性があります。
  - そのため、基本は **SSH接続での確認** を正とし、リソースに余裕がある場合のみOps Agent導入を検討します。

## 3. 実装イメージ (Implementation)

### 3.1 Flask Logger 設定 (`core/logging.py`)

Pythonの標準 `logging` モジュールを拡張し、JSONフォーマッターを適用。`before_request` でリクエストIDを生成・保持する。

### 3.2 フロントエンドへの通知

APIエラーレスポンス (`message`) を元に、UI上で **Toast Notification** (トースト通知) を表示する。

- `4xx`: Warning/Error 色でユーザーに修正を促す。
- `5xx`: Error 色で「システムエラーが発生しました」と表示。
