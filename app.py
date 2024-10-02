from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
import sys
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from sql import get_mongo_client

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
app = Flask(__name__)

# 初始化 MongoDB 連接
messages_collection = get_mongo_client()

# 設置 LINE Messaging API 的密鑰和 SECRET
LINE_CHANNEL_ACCESS_TOKEN = '0T7Bd7/DpIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XG1dlX2xQ+iVrq7sv00yDOKlCgZSUV7phm6KuGNQI4wAdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '433188037dc29d89488d1c0f2bcf1ea5'

line_bot_api = None
handler = None

# 檢查 LINE Messaging API 是否初始化成功
try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    print("LINE Bot API 初始化成功")
except LineBotApiError as e:
    print(f"LINE Bot API 初始化失敗: {e}")

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print(f"Request body: {body}")  # 打印請求體作為日誌

    # 使用 handler 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    # 處理訊息並儲存到資料庫
    data = json.loads(body)
    
    for event in data['events']:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            sender = event['source'].get('groupId') or event['source'].get('roomId') or event['source']['userId']
            message = event['message']['text']

            # 檢查 MongoDB 是否正確初始化
            if not messages_collection:
                print("MongoDB 尚未連接，無法儲存消息")
                continue

            # 如果訊息包含 "素材"，儲存到資料庫
            if "素材" in message:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"Received message: {message} from {sender} at {timestamp}")

                # 儲存到 MongoDB
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

# 定義用於回應訊息的函數
def reply_message(to, message):
    try:
        line_bot_api.push_message(to, TextSendMessage(text=message))
        print(f"Replying to {to} with message: {message}")
    except LineBotApiError as e:
        print(f"LineBotApiError: {e}")

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
    app.run(host='0.0.0.0', port=port)
