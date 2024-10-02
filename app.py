import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from sql import get_mongo_client

app = Flask(__name__)

# 初始化 MongoDB 連接
try:
    messages_collection = get_mongo_client()
    if messages_collection is None:
        raise Exception("Failed to connect to MongoDB")
    else:
        print("MongoDB connected successfully")
except Exception as e:
    print(f"Error initializing MongoDB: {e}")

# 從環境變數中讀取 LINE Messaging API 的密鑰和 SECRET
try:
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
        raise Exception("LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 沒有設置")

    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    print("LINE Bot API 初始化成功")
except LineBotApiError as e:
    print(f"LINE Bot API 初始化失敗: {e}")
except Exception as e:
    print(f"其他錯誤: {e}")

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    # 處理訊息並儲存到資料庫
    try:
        data = json.loads(body)
        for event in data['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                sender = event['source'].get('groupId') or event['source'].get('roomId') or event['source']['userId']
                message = event['message']['text']

                if not messages_collection:
                    print("MongoDB 尚未連接，無法儲存消息")
                    continue

                if "素材" in message:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    print(f"Received message: {message} from {sender} at {timestamp}")

                    try:
                        messages_collection.insert_one({
                            'sender': sender,
                            'message': message,
                            'timestamp': timestamp
                        })
                        print(f"Message saved to MongoDB: {message}")
                    except Exception as e:
                        print(f"Failed to insert message to MongoDB: {e}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 定義用於回應訊息的函數
def reply_message(to, message):
    try:
        line_bot_api.push_message(to, TextSendMessage(text=message))
        print(f"Replying to {to} with message: {message}")
    except LineBotApiError as e:
        print(f"LineBotApiError: {e}")

if __name__ == "__main__":
    try:
        port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Flask app failed to start: {e}")
