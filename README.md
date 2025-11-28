# Thesalo Gallery

iPhone で撮った犬の写真・動画を、自宅 PC 上の Flask アプリにアップロードして閲覧できるシンプルなギャラリーアプリです。

- Python + Flask
- Docker / docker-compose 対応
- アップロードされたファイルはローカルディスク (`uploads/`) に保存
- 同じ Wi-Fi に接続している iPhone からアクセス可能

---

## セットアップ（Docker なしで実行）

```bash
pip install -r requirements.txt
python app.py