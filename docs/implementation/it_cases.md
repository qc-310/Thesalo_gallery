# 結合テストケース (Integration Test Cases)

本ドキュメントは、テスト計画書および詳細設計に基づいて定義された、結合テスト (Integration Test) のケース一覧です。
Flaskのテストクライアントを使用し、APIエンドポイントのリクエストからレスポンスまで、およびDB/Celery(Eager)との連携を検証します。

## 1. 認証モジュール (Auth Blueprint)

**Target URL**: `/auth/*`

| ID | エンドポイント | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IT-AUTH-001` | `/auth/login` | GET | **ログインリダイレクト** | なし | GoogleログインURLへリダイレクト (Status 302) すること。 | 未実装 |
| `IT-AUTH-002` | `/auth/logout` | GET | **ログアウト** | ログイン状態のCookie | セッションがクリアされ、ログイン画面へリダイレクトすること。 | 未実装 |
| `IT-AUTH-003` | `/protected_route` | GET | **未認証アクセス** | クッキーなし | ログイン画面へリダイレクト、または 401/403 が返ること。 | 未実装 |

## 2. 家族モジュール (Family Blueprint)

**Target URL**: `/family/*`

| ID | エンドポイント | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IT-FAM-001` | `/family/create` | POST | **家族作成 (正常)** | `name="My Family"` | 家族が作成され、完了画面へリダイレクト、DBにレコードが存在すること。 | 未実装 |
| `IT-FAM-002` | `/family/list` | GET | **家族一覧取得** | ログイン済みユーザー | 所属する家族のHTMLリストが返却されること (Status 200)。 | 未実装 |

## 3. メディアモジュール (Media Blueprint)

**Target URL**: `/media/*`

| ID | エンドポイント | メソッド | ケース概要 | 入力 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IT-MEDIA-001` | `/media/upload` | POST | **画像アップロード (正常)** | valid `.jpg` file, `family_id` | Status 200/302。DBに `processing` で登録され、`uploads/` にファイル保存済みであること。 | 未実装 |
| `IT-MEDIA-002` | `/media/upload` | POST | **アップロード (不正)** | `.exe` file | Status 400 または バリデーションエラーメッセージ。DB登録なし。 | 未実装 |
| `IT-MEDIA-003` | `/media/{file_id}` | GET | **画像表示 (権限あり)** | 所属家族メンバー | 画像バイナリが返却される (Status 200, Content-Type: image/jpeg)。 | 未実装 |
| `IT-MEDIA-004` | `/media/{file_id}` | GET | **画像表示 (権限なし)** | 無関係なユーザー | Status 403 Forbidden。 | 未実装 |
| `IT-MEDIA-005` | `/media/{file_id}/thumb` | GET | **サムネイル表示** | 所属家族メンバー | サムネイル画像が返却される。動画の場合は生成済みサムネイル。 | 未実装 |

## 4. 全体フロー (Scenario)

| ID | ケース概要 | 手順 | 期待値 | ステータス |
| :--- | :--- | :--- | :--- | :--- |
| `IT-SCN-001` | **アップロード〜表示フロー** | 1. 家族作成 (`IT-FAM-001`)<br>2. 画像アップロード (`IT-MEDIA-001`)<br>3. 一覧ページで画像URL取得<br>4. 画像アクセス (`IT-MEDIA-003`) | 一連の操作がエラーなく完了し、アップロードした画像が表示できること。 | 未実装 |
