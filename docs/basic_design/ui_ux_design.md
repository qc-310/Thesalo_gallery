# 画面設計書 (UI/UX Design Document)

## 1. デザインコンセプト (Design Concept)

**テーマ**: "Wag & Warmth" (しっぽ振るような喜びと、家族の温かさ)

- **キーワード**: 親しみやすさ、プレミアム感、没入感
- **トーン＆マナー**:
  - ベース: シンプルでクリーンな白/オフホワイト (#FDFCF8)
  - アクセント: テラコッタオレンジ (#E07A5F)
  - フォント: Noto Sans JP / Inter

## 2. 画面遷移図 (Screen Transition Diagram)

サイト全体の画面構成と遷移フローを可視化します。

```mermaid
graph TD
    Login["ログイン画面"] --> |認証成功| Home["ホーム (タイムライン)"]
    
    Home --> |クリック| MediaDetail["メディア詳細 (モーダル/個別ページ)"]
    Home --> |メニュー| Upload["アップロード画面"]
    Home --> |メニュー| Profile["プロフィール/ペット切替"]
    Home --> |メニュー| Settings["設定画面"]
    
    MediaDetail --> |編集ボタン| EditMedia["メディア編集画面"]
    
    Profile --> |編集ボタン| ProfileEdit["プロフィール編集"]
    
    Settings --> FamilyManage["家族管理"]
    Settings --> Storage["ストレージ管理"]
```

## 3. ワイヤーフレーム (Page Layouts)

主要画面のレイアウト構成。

### 3.1 ホーム (Home) - PC View

```mermaid
graph TB
    subgraph Browser["ブラウザウィンドウ (PC)"]
        direction TB
        Header["ヘッダー<br/>(ロゴ | 検索 | 通知 | プロフィール)"]
        
        subgraph Body["メインエリア"]
            direction LR
            Side["サイドナビ<br/>(ホーム, アップロード, アルバム, 設定)"]
            Content["タイムラインコンテンツ<br/>(グリッド表示 / カレンダー表示)"]
        end
        
        Header --> Body
        Side ~~~ Content
    end
```

### 3.2 メディア詳細 (Media Detail) - PC View

```mermaid
graph TB
    subgraph Modal["詳細ビュー"]
        direction LR
        Media["画像/動画表示エリア<br/>(大きく表示)"]
        Meta["サイドパネル<br/>(キャプション | タグ | 日付 | 地図)"]
        
        Media ~~~ Meta
    end
```

### 3.3 スマホ表示 (Mobile View)

```mermaid
graph TB
    subgraph Mobile["スマホ画面"]
        direction TB
        Top["トップバー<br/>(検索 | 通知)"]
        Main["メインコンテンツ<br/>(リスト表示)"]
        Bottom["ボトムナビ<br/>(ホーム | 検索 | アップロード(+) | プロフィール)"]
        
        Top --> Main --> Bottom
    end
```

## 4. 操作フロー (User Flows)

主要なユーザーアクションの流れ。

### 4.1 アップロードフロー (Upload Flow)

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant UI as ブラウザ
    participant API as バックエンド
    participant DB as データベース
    participant Storage as ファイルストレージ

    User->>UI: ファイルをドラッグ&ドロップ
    UI->>UI: プレビュー表示 & メタデータ入力
    User->>UI: "投稿する" ボタンクリック
    activate UI
    UI->>API: アップロード開始 (POST /upload)
    API->>Storage: ファイル保存 (原本 & サムネ)
    API->>DB: メタデータ保存
    API-->>UI: 完了レスポンス
    deactivate UI
    UI-->>User: 完了通知 & タイムラインへリダイレクト
```

### 4.2 家族招待フロー (Family Invitation Flow)

```mermaid
sequenceDiagram
    actor Admin as 管理者
    participant UI as 設定画面
    actor Member as 招待メンバー

    Admin->>UI: "家族を招待" をクリック
    UI->>Admin: 招待リンクを生成して表示
    Admin->>Member: LINE/メールでリンク共有
    Member->>UI: リンクをクリック (ログイン)
    UI->>UI: 家族グループに参加処理
    UI-->>Member: "参加しました" 画面表示
```

## 5. デザインシステム (Design System)

### 5.1 カラーパレット

| Role | Color Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Primary** | Terracotta | `#E07A5F` | キーアクションボタン, アクティブアイコン |
| **Secondary** | Sage Green | `#81B29A` | 成功メッセージ, タグ背景 |
| **Background** | Off White | `#FDFCF8` | メイン背景 |
| **Surface** | Pure White | `#FFFFFF` | カード, モーダル背景 |
| **Text** | Charcoal | `#3D405B` | 見出し, 本文 |

### 5.2 コンポーネント

- **Media Card**: 角丸12px, ソフトな影, ホバーでズーム。
- **Buttons**:
  - Primary: 塗りつぶし (#E07A5F), 丸みのある形状。
  - Secondary: 枠線のみ。
- **Feedback**:
  - Loading: スケルトンスクリーン。
  - Success/Error: Toast通知。
