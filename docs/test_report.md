# テスト実施報告書

## 1. 概要

本ドキュメントは、Thesalo Gallery アプリケーションのリファクタリングに伴い実施されたユニットテストの結果をまとめたものです。

- **実施日**: 2025/12/22
- **テスト対象**: Backend Services (AuthService, FamilyService, MediaService) および Async Tasks (Celery)
- **テスト環境**: Docker (Web Container), pytest, SQLite (In-Memory)
- **結果概要**: 全 7 ケース実施、全て **PASS**

## 2. テスト環境構成

- **Framework**: pytest 7.4.3
- **Database**: SQLite (In-Memory)
- **Mocking**: pytest-mock (Celery Task, File I/O, Subprocess, Pillow)
- **Dependencies**: python-magic

## 3. テストケース詳細

### 3.1 AuthService (認証サービス)

| Test ID | テストケース名 | 検証内容 | 結果 |
| :--- | :--- | :--- | :--- |
| `UT-AUTH-001` | Googleユーザー登録 | 新規ユーザー情報(sub, email)が正しくDBに保存されること | **PASS** |
| `UT-AUTH-002` | Googleユーザーログイン | 既存ユーザーがログインした際、名前等の情報が更新されること | **PASS** |

### 3.2 FamilyService (家族管理サービス)

| Test ID | テストケース名 | 検証内容 | 結果 |
| :--- | :--- | :--- | :--- |
| `UT-FAM-001` | 家族作成 | ユーザーが家族を作成し、Admin権限が付与されること | **PASS** |
| `UT-FAM-002` | 家族一覧取得 | ユーザーが所属する家族一覧を取得できること | **PASS** |
| `UT-FAM-003` | メンバー追加 | 既存の家族に新しいメンバーを追加できること | **PASS** |

### 3.3 MediaService (メディア管理サービス)

| Test ID | テストケース名 | 検証内容 | 結果 |
| :--- | :--- | :--- | :--- |
| `UT-MEDIA-001` | メディアアップロード (正常系) | ファイル保存、DB登録(Pending)、非同期タスク呼び出しの連携 | **PASS** |
| `UT-MEDIA-002` | アップロード (不正な拡張子) | `.txt` ファイル等を拒否し `ValueError` を送出すること | **PASS** |
| `UT-MEDIA-003` | アップロード (ファイル名重複) | 同名ファイルが存在する場合、UUIDサフィックスを付与して保存すること | **PASS** |

### 3.4 Async Tasks (非同期タスク)

| Test ID | テストケース名 | 検証内容 | 結果 |
| :--- | :--- | :--- | :--- |
| `UT-TASK-001` | 画像リサイズ処理 | 巨大な画像を1920pxにリサイズし、ステータスを `ready` に更新すること | **PASS** |
| `UT-TASK-002` | 動画サムネイル生成 | `ffmpeg` コマンドを呼び出し、サムネイルパスをDBに保存すること | **PASS** |

## 4. 実行ログサマリ

```text
tests/test_services_core.py ..                                           [ 28%]
tests/test_services_media.py ...                                         [ 71%]
tests/test_tasks_media.py ..                                             [100%]

============================== 7 passed in 1.63s ===============================
```

## 5. 今後の課題

- APIエンドポイント (Blueprints) の結合テスト (Integration Tests)。
- フロントエンドを含めたE2Eテスト。
