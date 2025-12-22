# 単体テストケース (Unit Test Cases)

本ドキュメントは、テスト計画書および詳細設計に基づいて定義された、単体テスト (Unit Test) のケース一覧です。

## 1. 認証モジュール (Auth Module - AuthService)

| ID | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-AUTH-001` | `login_or_register_google_user` | **新規ユーザー登録** | 新規Googleユーザー情報 (email, sub) | DBに新しい `User` レコードが作成され、IDが付与されること。 | **実装済** (PASS) |
| `UT-AUTH-002` | `login_or_register_google_user` | **既存ユーザーログイン** | 既存Googleユーザー情報 (同一sub) | 既存の `User` レコードを返し、Mutableなフィールド (name, pic) が更新されること。 | **実装済** (PASS) |

## 2. 家族モジュール (Family Module - FamilyService)

| ID | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-FAM-001` | `create_family` | **家族作成** | 有効なUser, 名前="My Family" | 新しい `Family` が作成され、作成ユーザーが 'admin' として追加されること。 | **実装済** (PASS) |
| `UT-FAM-002` | `get_user_families` | **所属家族一覧取得** | User ID | ユーザーが所属する家族のリストが返されること。 | **実装済** (PASS) |
| `UT-FAM-003` | `add_member` | **メンバー追加** | Family ID, 新規ユーザーEmail | `family_members` テーブルに指定されたロールでユーザーが追加されること。 | **実装済** (PASS) |

## 3. メディアモジュール (Media Module - MediaService)

| ID | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-MEDIA-001` | `upload_media` | **正常アップロード (画像)** | 有効な `.jpg` ファイル | ファイルが `uploads/{fam}/{year}/{month}/` に保存され、DBステータスが `processing` となり、非同期タスクがトリガーされること。 | **実装済** (PASS) |
| `UT-MEDIA-002` | `upload_media` | **無効な拡張子** | `.txt` 拡張子のファイル | `ValueError` が発生し、ファイルは保存されないこと。 | **実装済** (PASS) |
| `UT-MEDIA-003` | `upload_media` | **ファイル名重複** | 既存のファイル名を持つファイル | ファイル名にUUID等のサフィックスが付与されて保存され、DBにもその名前で記録されること。 | **実装済** (PASS) |
| `UT-MEDIA-004` | `upload_media` | **MIMEタイプ判定** | 特定のシグネチャを持つファイル | DBに正しい `mime_type` (例: `image/jpeg`) が保存されること。 | **実装済** (PASS) |

## 4. 非同期タスク (Async Tasks - media_tasks)

| ID | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UT-TASK-001` | `process_media_task` | **画像リサイズ** | 有効な画像パス | 長辺が最大1920pxにリサイズされ、EXIFが保持され、DBステータスが `ready` に更新されること。 | **実装済** (PASS) |
| `UT-TASK-002` | `process_media_task` | **動画サムネイル生成** | 有効な動画パス | サムネイル画像が生成され、DBの `thumbnail_path` が更新されること。 | **実装済** (PASS) |
