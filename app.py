import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "thesalo_gallery.db"

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".heic"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


# =========================
# DB 初期化 & 同期
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            comment TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def sync_files_with_db():
    """
    uploads フォルダにあるのに DB に登録されていないファイルを
    自動で DB に登録する（既存ファイル救済用）
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # DBに既にあるファイル名一覧
    cur.execute("SELECT filename FROM photos")
    in_db = {row[0] for row in cur.fetchall()}

    # uploads フォルダの実ファイル
    for name in os.listdir(UPLOAD_FOLDER):
        fpath = UPLOAD_FOLDER / name
        if not fpath.is_file():
            continue
        if name in in_db:
            continue

        # 初回登録用にファイル更新日時を使う
        mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
        created_at = mtime.isoformat(timespec="seconds")

        cur.execute(
            "INSERT OR IGNORE INTO photos (filename, created_at, comment) VALUES (?, ?, ?)",
            (name, created_at, ""),
        )

    conn.commit()
    conn.close()


def allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS


def detect_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    return "other"


# アプリ起動時に1回だけ実行
init_db()
sync_files_with_db()


# =========================
# ルーティング
# =========================
@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 投稿日時の新しい順に並べる
    cur.execute(
        "SELECT id, filename, created_at, comment FROM photos ORDER BY datetime(created_at) DESC"
    )
    photos = cur.fetchall()
    conn.close()

    # type（image/video）も付与してテンプレートへ渡す
    photo_list = []
    for p in photos:
        p_type = detect_type(p["filename"])
        photo_list.append(
            {
                "id": p["id"],
                "filename": p["filename"],
                "created_at": p["created_at"],
                "comment": p["comment"] or "",
                "type": p_type,
            }
        )

    return render_template("index.html", photos=photo_list)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]
    comment = request.form.get("comment", "").strip()

    if file.filename == "":
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER / filename

        # 同名ファイルがある場合は _1, _2... を付けて回避
        if save_path.exists():
            stem = Path(filename).stem
            ext = Path(filename).suffix
            i = 1
            while True:
                new_name = f"{stem}_{i}{ext}"
                save_path = UPLOAD_FOLDER / new_name
                if not save_path.exists():
                    filename = new_name
                    break
                i += 1
            save_path = UPLOAD_FOLDER / filename

        # ファイル保存
        file.save(str(save_path))

        # DBへ登録
        created_at = datetime.now().isoformat(timespec="seconds")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO photos (filename, created_at, comment) VALUES (?, ?, ?)",
            (filename, created_at, comment),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    # ローカル／Docker共通で使える設定
    app.run(host="0.0.0.0", port=5000, debug=False)
