import os
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename

# =========================
# 設定
# =========================
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".heic"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


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


# =========================
# ルーティング
# =========================

@app.route("/", methods=["GET"])
def index():
    files = []
    for name in sorted(os.listdir(UPLOAD_FOLDER)):
        fpath = UPLOAD_FOLDER / name
        if not fpath.is_file():
            continue
        ftype = detect_type(name)
        files.append({"name": name, "type": ftype})
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER / filename
        # 同名ファイルがある場合は少し名前を変える
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
        file.save(str(save_path))

    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    # 0.0.0.0 でリッスンすると、同じLAN内の他の端末（iPhone）からアクセス可能になる
    app.run(host="0.0.0.0", port=5000, debug=True)
