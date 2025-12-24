# 統合テストケース (Integration Test Cases)

| ID | モジュール | シナリオ | 説明 | 期待結果 | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IT-AUTH-001 | Auth | Login Redirect | `/auth/login` にアクセスし、Google OAuthページへリダイレクトされるか確認 | ステータスコード302, Locationヘッダに `accounts.google.com` が含まれること | **実装済 (PASS)** |
| IT-AUTH-002 | Auth | Logout | ログイン状態で `/auth/logout` にアクセス | セッションがクリアされ、ログインページまたはインデックスへリダイレクトされること | **実装済 (PASS)** |
| IT-AUTH-003 | Auth | Unauthenticated Access | 未認証で保護されたルート（例: `/family/list`）にアクセス | ログインページへリダイレクトされること | **実装済 (PASS)** |
| IT-FAM-001 | Family | Create Family | ログインユーザーが新しい家族を作成するフロー | DBにFamilyレコードが作成され、ユーザーがAdminとして紐づくこと。Flashメッセージが表示されること。 | **実装済 (PASS)** |
| IT-FAM-002 | Family | List Families | 複数の家族に所属するユーザーが一覧を表示する | 所属する全ての家族名が表示されること | **実装済 (PASS)** |
| IT-MEDIA-001 | Media | Upload Media (Normal) | 家族IDを指定して有効な画像ファイルをアップロード | アップロード成功（200 OK またはリダイレクト）、DBにMediaレコード（Status: processing/ready）が作成されること | **実装済 (PASS)** |
| IT-MEDIA-002 | Media | Upload Invalid Extension | 許可されていない拡張子（例: .exe）をアップロード | エラー（400 Bad Request またはエラーメッセージ付きリダイレクト）となり、DB保存されないこと | **実装済 (PASS)** |
