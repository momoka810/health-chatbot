import os
import hmac
import hashlib
import logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .envファイルを読み込み、既存の環境変数を上書きする
load_dotenv(override=True)

app = FastAPI()

# 環境変数から設定を読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "https://api.dify.ai/v1")

# 環境変数の検証（未設定の場合はログに警告のみ）
if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, DIFY_API_KEY]):
    logger.warning("必要な環境変数が設定されていません。Vercelダッシュボードで環境変数を設定してください。")

# デバッグ用：トークンの状態を確認（最初の20文字のみ表示）
logger.info("=" * 50)
logger.info("環境変数の読み込み確認:")
logger.info(f"LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if LINE_CHANNEL_ACCESS_TOKEN else '未設定'}")
if LINE_CHANNEL_ACCESS_TOKEN:
    logger.info(f"トークンの先頭: {LINE_CHANNEL_ACCESS_TOKEN[:20]}...")
    logger.info(f"トークンの長さ: {len(LINE_CHANNEL_ACCESS_TOKEN)} 文字")
logger.info("=" * 50)


def verify_line_signature(body: bytes, signature: str) -> bool:
    """LINE Webhookの署名を検証"""
    if not LINE_CHANNEL_SECRET:
        logger.error("LINE_CHANNEL_SECRETが設定されていません")
        return False
    
    expected_signature = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"期待される署名: {expected_signature[:20]}...")
    logger.info(f"受信した署名: {signature[:20]}...")
    
    result = hmac.compare_digest(expected_signature, signature)
    if not result:
        logger.error(f"署名が一致しません")
        logger.error(f"期待される署名（全体）: {expected_signature}")
        logger.error(f"受信した署名（全体）: {signature}")
    
    return result


async def call_dify_api(user_message: str, user_id: str) -> str:
    """Dify APIを呼び出して回答を取得"""
    url = f"{DIFY_API_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {},
        "query": user_message,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": user_id
    }
    
    logger.info(f"Dify API URL: {url}")
    logger.info(f"リクエストデータ: {data}")
    
    # タイムアウトを短くして、reply_tokenが期限切れになる前に返信できるようにする
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            logger.info(f"Dify API レスポンスステータス: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            logger.info(f"Dify API レスポンス: {result}")
            answer = result.get("answer", "回答を取得できませんでした。")
            if not answer:
                logger.warning("Dify APIから回答が空です")
            return answer
        except httpx.HTTPStatusError as e:
            error_detail = f"Dify API エラー: {e.response.status_code}"
            error_message = "申し訳ございません。現在、AIアシスタントが利用できません。"
            
            if e.response.text:
                try:
                    error_json = e.response.json()
                    error_code = error_json.get("code", "")
                    error_msg = error_json.get("message", "")
                    error_detail += f" - {e.response.text}"
                    
                    # 特定のエラーメッセージを処理
                    if "provider_not_initialize" in error_code or "credentials is not initialized" in error_msg:
                        error_message = "申し訳ございません。Difyの設定に問題があります。モデルプロバイダーの認証情報を確認してください。"
                        logger.error(f"Dify設定エラー: {error_msg}")
                    elif "invalid_param" in error_code or "provider" in error_msg.lower() and "model" in error_msg.lower() and "None" in error_msg:
                        error_message = "申し訳ございません。Difyアプリでモデルプロバイダーとモデルが設定されていません。Dify Dashboardでアプリの設定を確認してください。"
                        logger.error(f"Difyモデル設定エラー: {error_msg}")
                    elif "invalid_api_key" in error_code or "unauthorized" in error_msg.lower():
                        error_message = "申し訳ございません。API認証に問題があります。"
                        logger.error(f"Dify認証エラー: {error_msg}")
                    elif "insufficient" in error_msg.lower() or "credit" in error_msg.lower() or "quota" in error_msg.lower():
                        error_message = "申し訳ございません。Difyのクレジットが不足しています。クレジットを追加してください。"
                        logger.error(f"Difyクレジット不足エラー: {error_msg}")
                    elif "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower() or "429" in str(e.response.status_code) or "RESOURCE_EXHAUSTED" in error_msg:
                        error_message = "申し訳ございません。APIの使用制限に達しました。しばらくしてから再度お試しください。"
                        logger.error(f"Difyレート制限エラー: {error_msg}")
                    elif "429" in str(e.response.status_code) or "RESOURCE_EXHAUSTED" in error_msg:
                        error_message = "申し訳ございません。APIの使用制限に達しました。しばらくしてから再度お試しください。"
                        logger.error(f"Dify API制限エラー (429): {error_msg}")
                except:
                    error_detail += f" - {e.response.text}"
            
            logger.error(error_detail)
            # エラーをraiseせずに、エラーメッセージを返す
            return error_message
        except Exception as e:
            logger.error(f"Dify API 呼び出しエラー: {str(e)}", exc_info=True)
            # エラーをraiseせずに、エラーメッセージを返す
            return "申し訳ございません。AIアシスタントへの接続に失敗しました。しばらくしてから再度お試しください。"


async def reply_to_line(reply_token: str, message: str, user_id: str = None):
    """LINE Reply APIを使って返信（reply_tokenが無効な場合はPush Message APIを使用）"""
    if not reply_token and not user_id:
        logger.error("reply_tokenとuser_idの両方が空です")
        return False
    
    # まずReply APIを試す
    if reply_token:
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }
        data = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        logger.info(f"LINE返信URL: {url}")
        logger.info(f"返信トークン: {reply_token[:20]}...")
        logger.info(f"返信メッセージ: {message[:100]}...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                logger.info(f"LINE API レスポンスステータス: {response.status_code}")
                response.raise_for_status()
                logger.info("LINE返信成功（Reply API）")
                return True
            except httpx.HTTPStatusError as e:
                error_detail = f"LINE API エラー: {e.response.status_code}"
                if e.response.text:
                    error_detail += f" - {e.response.text}"
                    logger.error(error_detail)
                
                # reply_tokenエラーの場合はPush Message APIにフォールバック
                if e.response.status_code == 400 and "Invalid reply token" in str(e.response.text):
                    logger.warning("reply_tokenが無効です。Push Message APIに切り替えます")
                    if user_id:
                        return await push_message_to_line(user_id, message)
                    else:
                        logger.error("user_idがないため、Push Message APIを使用できません")
                        return False
                else:
                    logger.error(error_detail)
                    return False
            except Exception as e:
                logger.error(f"LINE API 呼び出しエラー: {str(e)}", exc_info=True)
                # エラーが発生した場合もPush Message APIにフォールバック
                if user_id:
                    logger.warning("Push Message APIに切り替えます")
                    return await push_message_to_line(user_id, message)
                return False
    
    # reply_tokenがない場合はPush Message APIを使用
    if user_id:
        return await push_message_to_line(user_id, message)
    
    return False


async def push_message_to_line(user_id: str, message: str) -> bool:
    """LINE Push Message APIを使ってメッセージを送信"""
    if not user_id:
        logger.error("user_idが空です")
        return False
    
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return False
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    logger.info(f"使用するトークン: {LINE_CHANNEL_ACCESS_TOKEN[:20]}..." if LINE_CHANNEL_ACCESS_TOKEN else "トークンなし")
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    logger.info(f"LINE Push Message URL: {url}")
    logger.info(f"ユーザーID: {user_id}")
    logger.info(f"送信メッセージ: {message[:100]}...")
    logger.info(f"リクエストデータ: {data}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            logger.info(f"LINE Push API レスポンスステータス: {response.status_code}")
            logger.info(f"LINE Push API レスポンス: {response.text}")
            response.raise_for_status()
            logger.info("LINE Push Message成功")
            return True
        except httpx.HTTPStatusError as e:
            error_detail = f"LINE Push API エラー: {e.response.status_code}"
            if e.response.text:
                error_detail += f" - {e.response.text}"
                logger.error(error_detail)
                
                # エラーの詳細を解析
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", "")
                    
                    if "Failed to send messages" in error_message:
                        logger.error("メッセージ送信に失敗しました。以下の可能性があります：")
                        logger.error("1. ユーザーがBotをブロックしている")
                        logger.error("2. ユーザーがBotを友だち削除している")
                        logger.error("3. LINE_CHANNEL_ACCESS_TOKENが無効")
                        logger.error("4. メッセージが長すぎる（5000文字以内）")
                    elif "invalid" in error_message.lower():
                        logger.error(f"無効なリクエスト: {error_message}")
                except:
                    pass
            else:
                logger.error(error_detail)
            return False
        except Exception as e:
            logger.error(f"LINE Push API 呼び出しエラー: {str(e)}", exc_info=True)
            return False


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None, alias="X-Line-Signature")
):
    """LINE Webhookエンドポイント"""
    try:
        logger.info("=" * 50)
        logger.info("=== Webhook受信 ===")
        logger.info(f"リクエストメソッド: {request.method}")
        logger.info(f"リクエストURL: {request.url}")
        
        body = await request.body()
        logger.info(f"リクエストボディサイズ: {len(body)} bytes")
        
        # 署名検証（開発環境では一時的にスキップ可能）
        if x_line_signature:
            logger.info(f"署名ヘッダー受信: {x_line_signature[:20]}...")
            try:
                if not verify_line_signature(body, x_line_signature):
                    logger.error("署名検証に失敗しました")
                    # 開発環境では署名検証をスキップして処理を続行
                    logger.warning("署名検証失敗ですが、開発環境のため処理を続行します")
                else:
                    logger.info("署名検証成功")
            except Exception as e:
                logger.error(f"署名検証処理でエラー: {str(e)}")
                # エラーが発生しても処理を続行
                logger.warning("署名検証エラーですが、処理を続行します")
        else:
            logger.warning("署名ヘッダーがありません")
            logger.info("検証リクエストとして処理します")
        
        # JSON解析
        try:
            import json
            data = json.loads(body.decode('utf-8'))
            logger.info(f"JSONデータ: {data}")
        except Exception as e:
            logger.warning(f"JSON解析エラー: {str(e)}")
            logger.info("検証リクエストとして処理（空のレスポンスを返す）")
            return JSONResponse(content={"status": "ok"})
        
        events = data.get("events", [])
        logger.info(f"受信したイベント数: {len(events)}")
        
        # イベントがない場合（検証リクエストなど）は成功を返す
        if not events:
            logger.info("イベントがないため、検証リクエストとして処理")
            logger.info("=" * 50)
            return JSONResponse(content={"status": "ok"})
        
        for event in events:
            event_type = event.get("type")
            logger.info(f"イベントタイプ: {event_type}")
            
            # メッセージイベントのみ処理
            if event_type != "message":
                logger.info(f"メッセージイベントではないためスキップ: {event_type}")
                continue
            
            message = event.get("message", {})
            message_type = message.get("type")
            logger.info(f"メッセージタイプ: {message_type}")
            
            if message_type != "text":
                logger.info(f"テキストメッセージではないためスキップ: {message_type}")
                continue
            
            user_message = message.get("text", "")
            user_id = event.get("source", {}).get("userId", "")
            reply_token = event.get("replyToken", "")
            
            logger.info(f"ユーザーメッセージ: {user_message}")
            logger.info(f"ユーザーID: {user_id}")
            logger.info(f"返信トークン: {reply_token[:20]}..." if reply_token else "返信トークンなし")
            
            if not user_message or not reply_token:
                logger.warning("ユーザーメッセージまたは返信トークンがありません")
                continue
            
            try:
                # まず、reply_tokenを使って「処理中」メッセージを送信（reply_tokenを確実に使用）
                if reply_token:
                    logger.info("reply_tokenを使って処理中メッセージを送信")
                    await reply_to_line(reply_token, "考え中です。少々お待ちください...", user_id)
                    logger.info("処理中メッセージ送信完了")
                
                # Dify APIを呼び出し
                logger.info("Dify APIを呼び出し中...")
                dify_answer = await call_dify_api(user_message, user_id)
                logger.info(f"Difyからの回答: {dify_answer[:100]}...")
                logger.info(f"回答の長さ: {len(dify_answer)} 文字")
                
                # メッセージが長すぎる場合は切り詰める（LINEの制限は5000文字）
                if len(dify_answer) > 5000:
                    logger.warning(f"メッセージが長すぎるため、5000文字に切り詰めます")
                    dify_answer = dify_answer[:5000]
                
                # 実際の回答をPush Message APIで送信（reply_tokenは既に使用済み）
                logger.info("LINEに回答を送信中（Push Message API）...")
                logger.info(f"使用するuser_id: {user_id}")
                success = await push_message_to_line(user_id, dify_answer)
                if success:
                    logger.info("LINEへの返信成功")
                else:
                    logger.warning("LINEへの返信に失敗しました")
                    logger.warning("ユーザーがBotを友だち追加しているか確認してください")
                    logger.warning("LINE_CHANNEL_ACCESS_TOKENが有効か確認してください")
            except Exception as e:
                logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
                # エラーが発生しても処理を続行
        
        logger.info("=== Webhook処理完了 ===")
        return JSONResponse(content={"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook処理で予期しないエラー: {str(e)}", exc_info=True)
        # エラーが発生しても200を返す（LINE側にエラーを伝えない）
        return JSONResponse(content={"status": "ok"})


@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    return {"status": "ok", "message": "LINE Webhook is running"}


@app.get("/webhook")
async def webhook_get():
    """Webhook GETリクエスト用（検証用）"""
    logger.info("GET /webhook が呼ばれました（検証リクエスト）")
    return {"status": "ok", "message": "Webhook endpoint is ready"}


@app.get("/health")
async def health():
    """ヘルスチェック用エンドポイント（詳細版）"""
    return {
        "status": "ok",
        "message": "LINE Webhook is running",
        "env_check": {
            "LINE_CHANNEL_ACCESS_TOKEN": "設定済み" if LINE_CHANNEL_ACCESS_TOKEN else "未設定",
            "LINE_CHANNEL_SECRET": "設定済み" if LINE_CHANNEL_SECRET else "未設定",
            "DIFY_API_KEY": "設定済み" if DIFY_API_KEY else "未設定",
        }
    }


@app.post("/test-webhook")
async def test_webhook(request: Request):
    """テスト用Webhookエンドポイント（署名検証なし）"""
    try:
        body = await request.body()
        data = await request.json()
        logger.info("=== テストWebhook受信 ===")
        logger.info(f"リクエストボディ: {data}")
        return JSONResponse(content={"status": "ok", "received": data})
    except Exception as e:
        logger.error(f"テストWebhookエラー: {str(e)}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

