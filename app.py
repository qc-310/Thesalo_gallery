import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from pathlib import Path
from PIL import Image, ExifTags
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort, session
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

THUMB_FOLDER = UPLOAD_FOLDER / "thumbs"   # サムネ保存用
THUMB_FOLDER.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "thesalo_gallery.db"

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".heic"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key")

# Cookie Settings for Cloudflare/HTTPS
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# --- Auth Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# User Model (Simple)
class User(UserMixin):
    def __init__(self, id, email, name, is_admin=False):
        self.id = id
        self.email = email
        self.name = name
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    user_info = session.get('user_info')
    if not user_info:
        return None
    # Match against 'sub' or 'id'
    session_id = user_info.get('sub') or user_info.get('id')
    if user_id == session_id:
        email = user_info.get('email')
        is_admin = is_admin_email(email)
        return User(session_id, email, user_info['name'], is_admin)
    return None

def is_admin_email(email: str) -> bool:
    admin_emails_str = os.environ.get("ADMIN_EMAILS", "")
    if not admin_emails_str:
        return False
    admins = [e.strip() for e in admin_emails_str.split(",") if e.strip()]
    return email in admins

# --- Auth Routes ---
@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def authorize():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        # Handle cases where user rejected request or other OAuth errors
        return redirect(url_for('login_page'))

    # google.get('userinfo') failed because api_base_url is not set in server_metadata_url mode
    # We must use the absolute URL or rely on id_token (if parsed automatically, but let's stick to explicit fetch)
    resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
    user_info = resp.json()
    session['user_info'] = user_info
    # Google OIDC uses 'sub' as the unique identifier
    user_id = user_info.get('sub') or user_info.get('id')
    user_email = user_info.get('email')

    # Basic Email Restriction (Only if configured)
    allowed_emails_str = os.environ.get("ALLOWED_EMAILS", "")
    if allowed_emails_str:
        allowed = [e.strip() for e in allowed_emails_str.split(",") if e.strip()]
        if allowed and user_email not in allowed:
            # Not allowed
            return "Access Denied: Your email is not on the allowlist.", 403

    is_admin = is_admin_email(user_email)
    user = User(user_id, user_email, user_info['name'], is_admin)
    login_user(user)
    return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('user_info', None)
    return redirect(url_for('login_page'))

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
            captured_at TEXT,
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

def get_exif_date(file_path):
    """
    画像ファイルからEXIFの撮影日時を取得する。
    取得失敗や情報がない場合は None を返す。
    """
    try:
        with Image.open(file_path) as image:
            exif = image._getexif()
            if not exif:
                return None
            
            # DateTimeOriginal (36867) -> DateTimeDigitized (36868) -> DateTime (306) の順で探す
            tags = {
                36867: 'DateTimeOriginal',
                36868: 'DateTimeDigitized',
                306: 'DateTime'
            }
            
            for tag_id, name in tags.items():
                if tag_id in exif:
                    value = exif[tag_id]
                    # Format: "YYYY:MM:DD HH:MM:SS" -> "YYYY-MM-DDTHH:MM:SS"
                    try:
                        return value.replace(":", "-", 2).replace(" ", "T")
                    except:
                        continue
    except Exception as e:
        # ログにエラーを出力してデバッグしやすくする
        print(f"EXIF extraction failed for {file_path}: {e}")
        pass
    return None

def perform_exif_scan():
    """
    既存の画像のEXIFを再スキャンしてDBを更新する（内部処理用）
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # captured_at が NULL の画像を取得
    cur.execute("SELECT id, filename FROM photos WHERE captured_at IS NULL")
    rows = cur.fetchall()
    
    count = 0
    for row in rows:
        photo_id = row['id']
        filename = row['filename']
        file_path = UPLOAD_FOLDER / filename
        
        file_type = detect_type(filename)
        if file_type == 'image' and file_path.exists():
            date = get_exif_date(file_path)
            if date:
                cur.execute("UPDATE photos SET captured_at = ? WHERE id = ?", (date, photo_id))
                count += 1
    
    conn.commit()
    conn.close()
    return len(rows), count

@app.route("/api/scan_exif")
@login_required
def scan_exif():
    if not current_user.is_admin:
        return "Access Denied: Admin privileges required.", 403
    
    total, updated = perform_exif_scan()
    return f"Scanned {total} photos, updated {updated}."

def ensure_columns():
    """
    既存テーブルに新しいカラムを追加するマイグレーション関数
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(photos)")
    cols = [row[1] for row in cur.fetchall()]
    
    # thumbnail カラム追加
    if "thumbnail" not in cols:
        cur.execute("ALTER TABLE photos ADD COLUMN thumbnail TEXT")
    
    # captured_at カラム追加
    if "captured_at" not in cols:
        cur.execute("ALTER TABLE photos ADD COLUMN captured_at TEXT")
        
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


# アプリ起動時に実行
init_db()
ensure_columns()
sync_files_with_db()
perform_exif_scan()


# =========================
# ルーティング
# =========================
@app.route("/", methods=["GET"])
@login_required
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 初期表示: 24件だけ取得
    limit = 24
    offset = 0
    cur.execute(
        """
        SELECT id, filename, created_at, captured_at, comment, thumbnail 
        FROM photos 
        ORDER BY datetime(COALESCE(captured_at, created_at)) DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
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
                "captured_at": p["captured_at"],
                "comment": p["comment"] or "",
                "thumbnail": p["thumbnail"],
                "type": p_type,
            }
        )

    return render_template("index.html", photos=photo_list, user=current_user)

@app.route("/api/photos")
@login_required
def api_photos():
    page = request.args.get("page", 1, type=int)
    limit = 24
    offset = (page - 1) * limit

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, filename, created_at, captured_at, comment, thumbnail 
        FROM photos 
        ORDER BY datetime(COALESCE(captured_at, created_at)) DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )
    photos = cur.fetchall()
    conn.close()

    data = []
    for p in photos:
        p_type = detect_type(p["filename"])
        data.append({
            "id": p["id"],
            "filename": p["filename"],
            "comment": p["comment"] or "",
            "thumbnail": p["thumbnail"],
            "type": p_type,
            # URLを生成して返す
            "url": url_for('uploaded_file', filename=p['filename']),
            "thumb_url": url_for('thumbnail_file', filename=p['thumbnail']) if p['thumbnail'] else None,
            "edit_url": url_for('edit_photo', photo_id=p['id']),
            "delete_url": url_for('delete_photo', photo_id=p['id'])
        })
    
    return {"photos": data, "has_next": len(data) == limit}


@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if not current_user.is_admin:
        return "Access Denied: Admin privileges required.", 403

    if "file" not in request.files:
        return redirect(url_for("index"))

    files = request.files.getlist("file")
    # フロントエンドが動的に生成する comments リストを受け取る
    # input elements with name="comments"
    comments = request.form.getlist("comments")

    if not files or files[0].filename == "":
        return redirect(url_for("index"))

    # zip でファイルとコメントを同時にループ
    # コメント数がファイル数より少ない場合（またはその逆）は min(len) になるが
    # フロントエンドで対になるように生成しているので基本一致するはず
    # 足りない場合は空文字で埋めるロジックを入れると安全
    import itertools
    for file, comment in itertools.zip_longest(files, comments, fillvalue=""):
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
            captured_at = None

            if file_type == "image":
                # EXIF取得
                captured_at = get_exif_date(save_path)

            if file_type == "video":
                thumb_name = generate_video_thumbnail(filename)
                # 動画の撮影日時取得はライブラリ依存が激しいため今回は省略（作成日時=アップロード日時とする）

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO photos (filename, created_at, captured_at, comment, thumbnail) VALUES (?, ?, ?, ?, ?)",
                (filename, created_at, captured_at, comment.strip(), thumb_name),
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
@login_required
def edit_photo(photo_id: int):
    if not current_user.is_admin:
        return "Access Denied: Admin privileges required.", 403
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
@login_required
def delete_photo(photo_id: int):
    if not current_user.is_admin:
        return "Access Denied: Admin privileges required.", 403
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
