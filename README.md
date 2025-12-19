# Thesalo Gallery

Thesalo Gallery は、Flask ベースの画像・動画ギャラリーアプリケーションです。
画像や動画のアップロード、サムネイル自動生成、コメント機能などを備え、Docker を用いて簡単にデプロイできます。

## 機能概要

*   **ファイルアップロード**: 画像 (`.png`, `.jpg`, `.jpeg`, `.gif`, `.heic`) および動画 (`.mp4`, `.mov`, `.avi`, `.mkv`) のアップロードに対応。
*   **サムネイル生成**: アップロードされた動画から `ffmpeg` を使用して自動的にサムネイル画像を生成します。
*   **DB同期**: アップロードフォルダ内のファイルと SQLite データベースを自動的に同期（未登録ファイルの登録など）。
*   **ギャラリー表示**: 投稿日時の新しい順に写真・動画を表示します。
*   **詳細・編集**: 個別ページでの閲覧、コメントの編集、ファイルの削除が可能。
*   **Docker 対応**: `docker-compose` を使って手軽に環境構築が可能。

## 技術スタック

*   **Backend**: Python 3 (Flask)
*   **Database**: SQLite (`thesalo_gallery.db`)
*   **Media Processing**: ffmpeg (動画サムネイル生成用)
*   **Infra**: Docker, Docker Compose

## ディレクトリ構成

```
.
├── app.py                # アプリケーションのメインロジック (Flask)
├── Dockerfile            # Docker イメージ定義
├── docker-compose.yml    # Docker コンテナ構成定義
├── requirements.txt      # Python 依存ライブラリ
├── templates/            # HTML テンプレート (Jinja2)
│   ├── index.html        # ギャラリー一覧
│   ├── edit.html         # 編集画面
│   └── ...
├── uploads/              # アップロードされたファイル (永続化対象)
│   └── thumbs/           # 生成されたサムネイル
└── thesalo_gallery.db    # SQLite データベースファイル
```

## セットアップ & 実行方法

### Docker を使用する場合 (推奨)

Docker および Docker Compose がインストールされている環境で以下を実行してください。

```bash
# ビルド＆起動
docker-compose up --build -d
```

起動後、ブラウザで `http://localhost:5000` にアクセスしてください。

### ローカル環境で直接実行する場合

Python 3 と `ffmpeg` がインストールされている必要があります。

1.  **依存ライブラリのインストール**
    ```bash
    pip install -r requirements.txt
    ```

2.  **ffmpeg の確認**
    `ffmpeg` コマンドがパスに通っていることを確認してください（動画サムネイル生成に必要です）。

3.  **アプリの起動**
    ```bash
    python app.py
    ```

## API / ルーティング

| メソッド | パス | 説明 |
| :--- | :--- | :--- |
| `GET` | `/` | ギャラリー一覧（トップページ） |
| `POST` | `/upload` | ファイルのアップロード処理 |
| `GET` | `/uploads/<path>` | アップロードされたファイルの配信 |
| `GET` | `/thumbs/<path>` | サムネイル画像の配信 |
| `GET/POST`| `/photo/<id>/edit` | 画像の詳細表示・コメント編集 |
| `POST` | `/photo/<id>/delete`| 画像・動画の削除 |

## 注意事項

*   `uploads/` ディレクトリは Docker コンテナ内でボリュームマウントされているため、コンテナを削除してもデータは保持されます。
*   初めて起動する際、`thesalo_gallery.db` や `uploads/` フォルダが存在しない場合は自動的に作成されます。