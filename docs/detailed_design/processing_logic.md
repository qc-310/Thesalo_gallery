# 処理ロジック設計書 (Processing Logic Design Document)

## 1. 非同期処理モデル概要 (Async Processing Model Overview)

本システムでは、ユーザー体験を阻害しないため、時間の掛かる処理（画像・動画変換、AI解析）を **Celery Task** として非同期実行します。

### ステータス遷移

`media.status` カラムの遷移フロー:

1. `processing` (Upload直後)
2. `ready` (全処理完了・公開可能)
3. `error` (処理失敗)

## 2. 詳細フロー (Detailed Flows)

### 2.1 メディアアップロードフロー (Media Upload Flow)

ユーザーがブラウザからファイルをアップロードした際の処理。

**Actors**: User, Web App (Flask), DB, Celery, Storage

1. **Request**: User -> `POST /api/v1/media` (Multipart form)
2. **Validation**: Flaskがファイル形式、サイズ(1GB以下)をチェック。
3. **Local Save**: Flaskが `uploads/{family_id}/temp/` に一時保存。
4. **DB Insert**: `media` テーブルに `status='processing'` でレコード作成。
5. **Enqueue**: Flaskが `process_media_task(media_id)` をCeleryに投入。
6. **Response**: User <- `202 Accepted` (media_idを含む)。

### 2.2 メディア加工・解析フロー (Media Processing Task)

Celery Workerが実行する処理。

**Task**: `process_media_task(media_id)`

1. **Fetch**: DBから `media` レコード取得。
2. **Determine Type**:
    * **Image**:
        1. **Exif**: 撮影日時、位置情報を抽出・DB更新。
        2. **Normalize**: HEIC/HEIFならJPEG/PNGに変換。
        3. **Resize**: 長辺1920pxにリサイズ。
        4. **Thumbnail**: 縦横300pxのWebPサムネイル生成。
        5. **Save**: `uploads/{family_id}/{yyyy}/{mm}/` に移動・保存。
    * **Video**:
        1. **Metadata**: 動画長、解像度取得。
        2. **Transcode**: FFmpegでHLS (.m3u8 + .ts) に変換（ストリーミング用）。
        3. **Thumbnail**: 先頭フレームからサムネ生成。
        4. **Save**: 同上。
3. **Clean up**: 一時ファイルを削除。
4. **Chain AI Task**: 続けて `detect_faces_task(media_id)` を呼び出し（Imageの場合）。
5. **Update DB**: `status='ready'`, `file_path` 等を更新。

### 2.3 AI顔検出フロー (AI Face Detection Task)

画像から顔を検出し、タグ付け等の準備を行う。

**Task**: `detect_faces_task(media_id)`

1. **Load**: 画像ファイルをロード (OpenCV/PIL)。
2. **Detect**: カスケード分類器またはDeep Learningモデルで顔座標を検出。
3. **Crop & Save**: 検出された顔領域をクロップし、`faces/` ディレクトリに保存（学習/クラスタリング用）。
4. **Clustering (Future Work)**: 類似顔をグループ化し、`User` または `PetProfile` との紐付け候補を作成。

## 3. バリデーションロジック (Validation Logic)

データの整合性とセキュリティを担保するため、以下の3層でバリデーションを実施します。

### 3.1 入力値バリデーション (Input Validation)

APIのリクエストボディおよびクエリパラメータの形式チェック。**Pydantic** モデルを用いて定義・検証することを推奨します。

* **必須チェック**: 必須フィールドの欠落チェック。
* **型・フォーマット**: UUID形式、Email形式、日付形式 (`YYYY-MM-DD`)。
* **値の範囲・長さ**:
  * `name`: 1〜100文字。
  * `description`: 最大1000文字。
  * `limit`: ページネーション上限 (Max 100)。

### 3.2 ファイルバリデーション (File Validation)

アップロードされたファイルの安全性チェック。

* **拡張子制限**: `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov` のみ許可。
* **Magic Number Check**: ファイルヘッダー（バイナリ先頭）を読み込み、拡張子と実際のファイルタイプが一致するか検証（`python-magic` 等を使用）。
* **サイズ制限**: Webサーバー (Nginx) とアプリ (Flask) の両方で上限 (1GB) を適用。

### 3.3 ビジネスルールバリデーション (Business Logic Validation)

Service Layerで実行する、状態や権限に依存するチェック。

* **権限チェック**: 操作対象の `family_id` に、ユーザーが `family_members` として所属しているか。
* **重複チェック**: 同じメールアドレスのメンバー招待など。
* **クォータ**: (将来的に) ストレージ容量制限など。
