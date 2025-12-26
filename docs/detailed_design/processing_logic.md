# 処理ロジック設計書 (Processing Logic Design Document)

## 1. 非同期処理モデル概要 (Async Processing Model Overview)

本システムでは、ユーザー体験を阻害しないため、時間の掛かる処理（画像・動画変換、AI解析）を **Cloud Tasks** (またはローカル開発環境では同期実行) として処理します。

### ステータス遷移

`media.status` カラムの遷移フロー:

1. `processing` (Upload直後)
2. `ready` (全処理完了・公開可能)
3. `error` (処理失敗)

## 2. 詳細フロー (Detailed Flows)

### 2.1 メディアアップロードフロー (Media Upload Flow)

ユーザーがブラウザからファイルをアップロードした際の処理。

**Actors**: User, Web App (Flask), DB (PostgreSQL), Cloud Tasks, Storage (GCS/Local)

1. **Request**: User -> `POST /media/upload` (Multipart form)
2. **Validation**: Flaskがファイル形式、サイズをチェック。
3. **Save**:
    - **Local**: `uploads/galleries/{YYYY}/{MM}/` に保存。
    - **Cloud**: GCSへ直接アップロード (またはWebサーバー経由でGCSへ保存)。
4. **DB Insert**: `media` テーブルに `status='processing'` でレコード作成。
5. **Enqueue/Process**:
    - **Local (Sync)**: その場で画像処理関数を実行。
    - **Cloud (Async)**: Cloud Tasks にタスクを追加 (HTTP Target: `/tasks/handlers/process-media`)。
6. **Response**: User <- `200 OK` (media_idを含む)。

### 2.2 メディア加工・解析フロー (Media Processing Task)

Cloud Tasks Worker (Flask Endpoint) が実行する処理。

**Endpoint**: `POST /tasks/handlers/process-media`
**Payload**: `{"media_id": "..."}`

1. **Fetch**: DBから `media` レコード取得。
2. **Download**: Storage (GCS) から一時領域へファイルをダウンロード。
3. **Determine Type**:
    - **Image**:
        1. **Exif**: 撮影日時、位置情報を抽出・DB更新。
        2. **Normalize**: HEIC/HEIFならJPEG/PNGに変換。
        3. **Resize**: 長辺1920pxにリサイズ。
        4. **Thumbnail**: 縦横300pxのWebPサムネイル生成。
        5. **Save**: Storageに保存（オリジナル上書き、または最適化版として保存）。
    - **Video**:
        1. **Metadata**: 動画長、解像度取得。
        2. **Transcode**: FFmpegでHLS (.m3u8 + .ts) に変換（ストリーミング用）。
        3. **Thumbnail**: 先頭フレームからサムネ生成。
        4. **Save**: Storageに保存。
4. **Update DB**: `status='ready'`, `width`, `height`, `file_size` 等を更新。

### 2.3 AI顔検出フロー (AI Face Detection Task)

(Future Implementation) 画像から顔を検出し、タグ付け等の準備を行う。
既存フローと同様に、Cloud Tasksの別キューまたはチェーン実行として実装予定。

## 3. バリデーションロジック (Validation Logic)

データの整合性とセキュリティを担保するため、以下の3層でバリデーションを実施します。

### 3.1 入力値バリデーション (Input Validation)

APIのリクエストボディおよびクエリパラメータの形式チェック。**Pydantic** または **Marshmallow** を推奨。

- **必須チェック**: 必須フィールドの欠落チェック。
- **型・フォーマット**: UUID形式、Email形式、日付形式 (`YYYY-MM-DD`)。
- **値の範囲・長さ**:
  - `name`: 1〜100文字。
  - `description`: 最大1000文字。

### 3.2 ファイルバリデーション (File Validation)

アップロードされたファイルの安全性チェック。

- **拡張子制限**: `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov` のみ許可。
- **Magic Number Check**: ファイルヘッダー（バイナリ先頭）を読み込み、拡張子と実際のファイルタイプが一致するか検証（`python-magic` 等を使用）。
- **サイズ制限**:
  - Local/Cloud Run: Nginx/Gunicorn/Flaskの設定で上限 (1GB) を適用。

### 3.3 ビジネスルールバリデーション (Business Logic Validation)

Service Layerで実行する、状態や権限に依存するチェック。

- **権限チェック**: `uploader_id` が現在のユーザーと一致するか（削除・編集時）、または `role` が `owner` であるか。
- **重複チェック**: 同じメールアドレスのメンバー招待など。
