import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

THUMB_FOLDER = UPLOAD_FOLDER / "thumbs"   # サムネ保存用
THUMB_FOLDER.mkdir(exist_ok=True)

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
    自動で DB に登録する + 動画はサムネも作る
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT filename, thumbnail FROM photos")
    in_db = {row[0]: row[1] for row in cur.fetchall()}

    for name in os.listdir(UPLOAD_FOLDER):
        fpath = UPLOAD_FOLDER / name
        if not fpath.is_file():
            continue

        file_type = detect_type(name)

        # DB未登録の場合は新規登録
        if name not in in_db:
            # 既存ファイルは更新日時を created_at に使う
            mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
            created_at = mtime.isoformat(timespec="seconds")

            thumb_name = None
            if file_type == "video":
                thumb_name = generate_video_thumbnail(name)

            cur.execute(
                "INSERT OR IGNORE INTO photos (filename, created_at, comment, thumbnail) VALUES (?, ?, ?, ?)",
                (name, created_at, "", thumb_name),
            )

        # すでに登録済みで thumbnail が空の動画はサムネを補完
        elif file_type == "video" and not in_db[name]:
            thumb_name = generate_video_thumbnail(name)
            if thumb_name:
                cur.execute(
                    "UPDATE photos SET thumbnail = ? WHERE filename = ?",
                    (thumb_name, name),
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

def ensure_thumbnail_column():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(photos)")
    cols = [row[1] for row in cur.fetchall()]
    if "thumbnail" not in cols:
        cur.execute("ALTER TABLE photos ADD COLUMN thumbnail TEXT")
        conn.commit()
    conn.close()

def generate_video_thumbnail(filename: str) -> str | None:
    """
    動画ファイルから 1 フレーム切り出してサムネ画像を作る。
    成功したらサムネファイル名を返す / 失敗時は None。
    """
    video_path = UPLOAD_FOLDER / filename
    thumb_name = f"{Path(filename).stem}_thumb.jpg"
    thumb_path = THUMB_FOLDER / thumb_name

    # すでに存在するなら作り直さない
    if thumb_path.exists():
        return thumb_name

    # ffmpegコマンドで1秒地点のフレームを切り出し
    cmd = [
        "ffmpeg",
        "-y",                # 上書き
        "-ss", "00:00:01.000",
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if thumb_path.exists():
            return thumb_name
    except Exception as e:
        print(f"[WARN] thumbnail generation failed for {filename}: {e}")

    return None


# アプリ起動時に1回だけ実行
init_db()
ensure_thumbnail_column()
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
    "SELECT id, filename, created_at, comment, thumbnail FROM photos ORDER BY datetime(created_at) DESC"
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
                "thumbnail": p["thumbnail"],
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

        # 同名回避
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

        file.save(str(save_path))

        created_at = datetime.now().isoformat(timespec="seconds")
        file_type = detect_type(filename)

        thumb_name = None
        if file_type == "video":
            thumb_name = generate_video_thumbnail(filename)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO photos (filename, created_at, comment, thumbnail) VALUES (?, ?, ?, ?)",
            (filename, created_at, comment, thumb_name),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))



@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/thumbs/<path:filename>")
def thumbnail_file(filename):
    return send_from_directory(str(THUMB_FOLDER), filename)

@app.route("/photo/<int:photo_id>/edit", methods=["GET", "POST"])
def edit_photo(photo_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST":
        # コメント更新
        comment = request.form.get("comment", "").strip()
        cur.execute(
            "UPDATE photos SET comment = ? WHERE id = ?",
            (comment, photo_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    # GET のときは編集画面表示
    cur.execute("SELECT * FROM photos WHERE id = ?", (photo_id,))
    photo = cur.fetchone()
    conn.close()

    if photo is None:
        abort(404)

    p_type = detect_type(photo["filename"])
    return render_template("edit.html", photo=photo, type=p_type)

@app.route("/photo/<int:photo_id>/delete", methods=["POST"])
def delete_photo(photo_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ファイル名とサムネ名を取得
    cur.execute("SELECT filename, thumbnail FROM photos WHERE id = ?", (photo_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("index"))

    filename = row["filename"]
    thumb = row["thumbnail"]

    # DB から削除
    cur.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()

    # 実ファイル削除（存在チェック付き）
    file_path = UPLOAD_FOLDER / filename
    if file_path.exists():
        file_path.unlink()

    if thumb:
        thumb_path = THUMB_FOLDER / thumb
        if thumb_path.exists():
            thumb_path.unlink()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # ローカル／Docker共通で使える設定
    app.run(host="0.0.0.0", port=5000, debug=False)
