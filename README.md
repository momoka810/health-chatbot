# LINE × Dify Chat Bot連携プロジェクト

Difyで作成したChat Bot（栄養サポートBot: たすだけヘルス）をLINE Messaging APIと連携し、LINE上でチャットできるようにするプロジェクトです。

## 📋 目次

- [概要](#概要)
- [機能](#機能)
- [技術スタック](#技術スタック)
- [フォルダ構成](#フォルダ構成)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [アーキテクチャ](#アーキテクチャ)
- [API仕様](#api仕様)
- [デプロイ方法](#デプロイ方法)
- [トラブルシューティング](#トラブルシューティング)
- [注意事項](#注意事項)

## 📖 概要

このプロジェクトは、FastAPIを使用してLINE Messaging APIとDify APIを連携するWebhookサーバーです。LINEから送信されたメッセージをDify APIに送信し、生成された回答をLINEに返信します。

### 主な特徴

- LINE Webhookを受信し、ユーザーのメッセージを処理
- Dify APIを呼び出してAI回答を生成
- LINE Reply APIとPush Message APIの両方に対応
- エラーハンドリングとログ機能を実装
- 署名検証によるセキュリティ対策

## 🎯 機能

- **メッセージ受信**: LINEから送信されたテキストメッセージを受信
- **AI回答生成**: Dify APIを使用してユーザーの質問に対する回答を生成
- **自動返信**: 生成された回答をLINEに自動返信
- **エラーハンドリング**: 各種エラーを適切に処理し、ユーザーに分かりやすいメッセージを返信
- **ログ機能**: 詳細なログを出力し、デバッグを容易にする

## 🛠 技術スタック

- **Python 3.9+**
- **FastAPI**: Webフレームワーク
- **Uvicorn**: ASGIサーバー
- **httpx**: 非同期HTTPクライアント
- **python-dotenv**: 環境変数管理
- **LINE Messaging API**: LINE Bot機能
- **Dify API**: AIチャットボット機能

## 📁 フォルダ構成

```
5-4-2_Dify 実践課題②/
├── main.py              # FastAPIアプリケーション（メインコード）
├── requirements.txt     # Python依存パッケージ一覧
├── .env                 # 環境変数（.gitignoreに追加推奨）
├── .env.example         # 環境変数のテンプレート
└── README.md           # このファイル
```

## 🚀 セットアップ

### 前提条件

- Python 3.9以上がインストールされていること
- LINE Developersアカウント
- Difyアカウント
- ngrok（ローカル開発用）

### 1. リポジトリのクローンまたはダウンロード

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/5-4-2_Dify 実践課題②"
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または

```bash
pip3 install -r requirements.txt
```

### 3. 必要なAPIキーの取得

#### LINE Messaging API

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. 新しいプロバイダーを作成（初回のみ）
3. チャネルを作成（Messaging APIチャネル）
4. 以下の情報を取得：
   - **チャネルアクセストークン（長期）**: `LINE_CHANNEL_ACCESS_TOKEN`
   - **チャネルシークレット**: `LINE_CHANNEL_SECRET`

#### Dify API

1. [Dify Dashboard](https://dify.ai/) にログイン
2. アプリを作成（チャットボット）
3. モデルプロバイダーを設定（OpenAI、Google Gemini、Hugging Faceなど）
4. アプリの設定でモデルを選択
5. 右上のアカウントアイコン → 「API Keys」からAPI Keyを取得
6. 取得したAPI Keyを `DIFY_API_KEY` として使用

### 4. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の値を設定：

```bash
# LINE Messaging API設定
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# Dify API設定
DIFY_API_KEY=your_dify_api_key_here
DIFY_API_BASE_URL=https://api.dify.ai/v1
```

**重要**: 
- 値の前後にスペースや引用符は不要です
- `.env`ファイルはGitにコミットしないでください（機密情報が含まれます）

## 💻 使用方法

### ローカル開発環境での起動

#### 1. サーバーの起動

```bash
python3 main.py
```

または

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが正常に起動すると、以下のようなメッセージが表示されます：

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 2. ngrokの起動（別のターミナル）

LINE WebhookはHTTPS接続が必要なため、ローカル開発時はngrokを使用します：

```bash
ngrok http 8000
```

ngrokが起動すると、以下のような表示が出ます：

```
Forwarding  https://xxxx-xxxx.ngrok-free.dev -> http://localhost:8000
```

このHTTPS URLをコピーしてください。

#### 3. LINE DevelopersコンソールでWebhook URLを設定

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. あなたのチャネルを選択
3. 「Messaging API」タブを開く
4. 「Webhook URL」に以下を設定：
   ```
   https://xxxx-xxxx.ngrok-free.dev/webhook
   ```
   **重要**: 末尾に `/webhook` を必ず追加してください
5. 「検証」ボタンをクリックして接続確認
6. 「Webhookの利用」を「利用する」に設定
7. 「応答メッセージ」を「無効」に設定（Botが応答するため）

#### 4. LINEアプリでBotを友だち追加

1. LINEアプリを開く
2. Botを検索して友だち追加
3. Botにメッセージを送信

#### 5. 動作確認

LINEアプリでBotにメッセージを送信すると、以下の流れで動作します：

1. LINEからWebhookが送信される
2. サーバーが「考え中です。少々お待ちください...」を返信
3. Dify APIを呼び出して回答を生成
4. 生成された回答をLINEに送信

## 🏗 アーキテクチャ

```
LINEアプリ
    ↓ (メッセージ送信)
LINE Messaging API
    ↓ (Webhook POST)
FastAPIサーバー (/webhook)
    ↓ (ユーザーメッセージ)
Dify API
    ↓ (AI回答)
FastAPIサーバー
    ↓ (回答)
LINE Reply API / Push Message API
    ↓ (返信)
LINEアプリ
```

### 処理フロー

1. **Webhook受信**: LINEからPOSTリクエストを受信
2. **署名検証**: LINE Webhookの署名を検証（セキュリティ）
3. **イベント解析**: メッセージイベントを抽出
4. **即座に返信**: reply_tokenを使用して「処理中」メッセージを送信
5. **Dify API呼び出し**: ユーザーメッセージをDify APIに送信
6. **回答取得**: Dify APIから回答を取得
7. **LINE返信**: Push Message APIを使用して回答を送信

## 📡 API仕様

### POST /webhook

LINE Webhookを受信するエンドポイント

**リクエストヘッダー:**
- `X-Line-Signature`: LINE Webhookの署名（署名検証用）

**リクエストボディ:**
```json
{
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "text": "ユーザーのメッセージ"
      },
      "source": {
        "userId": "ユーザーID"
      },
      "replyToken": "返信トークン"
    }
  ]
}
```

**レスポンス:**
```json
{
  "status": "ok"
}
```

### GET /

ヘルスチェック用エンドポイント

**レスポンス:**
```json
{
  "status": "ok",
  "message": "LINE Webhook is running"
}
```

### GET /health

環境変数の設定状況を確認するエンドポイント

**レスポンス:**
```json
{
  "status": "ok",
  "message": "LINE Webhook is running",
  "env_check": {
    "LINE_CHANNEL_ACCESS_TOKEN": "設定済み",
    "LINE_CHANNEL_SECRET": "設定済み",
    "DIFY_API_KEY": "設定済み"
  }
}
```

## 🚢 デプロイ方法

### Herokuへのデプロイ

1. Herokuアカウントを作成
2. Heroku CLIをインストール
3. プロジェクトをHerokuにデプロイ：

```bash
heroku create your-app-name
git push heroku main
```

4. 環境変数を設定：

```bash
heroku config:set LINE_CHANNEL_ACCESS_TOKEN=your_token
heroku config:set LINE_CHANNEL_SECRET=your_secret
heroku config:set DIFY_API_KEY=your_key
```

5. LINE DevelopersコンソールでWebhook URLを設定：
   - Webhook URL: `https://your-app-name.herokuapp.com/webhook`

### その他のプラットフォーム

- **AWS Lambda**: Serverless Frameworkを使用
- **Google Cloud Run**: Dockerコンテナとしてデプロイ
- **Azure App Service**: Pythonアプリとしてデプロイ

## 🔧 トラブルシューティング

### Webhook検証が失敗する

**症状**: LINE Developersコンソールで「検証」ボタンをクリックしてもエラーが出る

**解決方法**:
1. サーバーが起動しているか確認
2. ngrokが起動しているか確認
3. Webhook URLの末尾に `/webhook` があるか確認
4. ngrokのURLとLINE DevelopersコンソールのURLが一致しているか確認

### 401 Unauthorizedエラー

**症状**: `Authentication failed. Confirm that the access token in the authorization header is valid.`

**解決方法**:
1. LINE Developersコンソールでチャネルアクセストークンを再発行
2. `.env`ファイルの`LINE_CHANNEL_ACCESS_TOKEN`を更新
3. サーバーを再起動
4. システム環境変数に古いトークンが設定されていないか確認

### Dify APIエラー

**症状**: `Model gpt-4 credentials is not initialized` または `provider\n  Input should be a valid string`

**解決方法**:
1. Dify Dashboardでアプリの設定を確認
2. モデルプロバイダーが選択されているか確認
3. モデルが選択されているか確認
4. モデルプロバイダーのAPI Keyが設定されているか確認

### LINE返信が失敗する

**症状**: `Failed to send messages`

**解決方法**:
1. LINEアプリでBotを友だち追加しているか確認
2. `LINE_CHANNEL_ACCESS_TOKEN`が有効か確認
3. メッセージが5000文字以内か確認

### 環境変数が読み込まれない

**症状**: サーバーのログで「未設定」と表示される

**解決方法**:
1. `.env`ファイルが正しい場所にあるか確認
2. `.env`ファイルの形式が正しいか確認（スペース・引用符がないか）
3. サーバーを再起動
4. `load_dotenv(override=True)`が設定されているか確認

## ⚠️ 注意事項

### セキュリティ

- `.env`ファイルはGitにコミットしないでください
- API Keyやトークンは機密情報です。他人に共有しないでください
- 本番環境では、環境変数を適切に管理してください

### 制限事項

- LINEのreply_tokenは30秒以内に使用する必要があります
- メッセージは5000文字以内に制限されています
- Dify APIの呼び出しには時間がかかる場合があります

### ベストプラクティス

- 定期的にAPI Keyやトークンを更新してください
- エラーログを監視し、問題を早期に発見してください
- 本番環境では、ログの記録とモニタリングを実装してください

## 📝 ライセンス

このプロジェクトは教育目的で作成されています。

## 👤 作成者

AIエンジニア講座 実践課題②

## 🙏 謝辞

- [LINE Messaging API](https://developers.line.biz/ja/docs/messaging-api/)
- [Dify](https://dify.ai/)
- [FastAPI](https://fastapi.tiangolo.com/)
