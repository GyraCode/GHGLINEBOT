from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
import os
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError

app = Flask(__name__)

# LINE Messaging API 的密鑰和 SECRET
LINE_CHANNEL_ACCESS_TOKEN = '0T7Bd7/DPIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXG114xQQpV4t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '433188037dc29d89488d1c0f2bcf1ea5'

# 初始化 LineBotApi 和 WebhookHandler
line_bot_api = None
handler = None

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    print("LINE Bot API 和 WebhookHandler 初始化成功")
except LineBotApiError as e:
    print(f"LINE Bot API 初始化失敗: {e}")

# 設置 MongoDB 連接
try:
    client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['Cluster0']
    messages_collection = db['messages']
    print("MongoDB 連接成功")
except Exception as e:
    print(f"MongoDB 連接失敗: {e}")

# 驗證 LINE Webhook 的請求簽名
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)  # 使用 WebhookHandler 來驗證簽名
        data = json.loads(body)
        print(f"Received request body: {data}")  # 打印收到的請求

        for event in data['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                # 提取 replyToken
                if 'replyToken' in event:
                    reply_token = event['replyToken']
                    print(f"Reply token: {reply_token}")  # 日誌輸出 replyToken
                else:
                    print("No replyToken found")
                    continue

                # 處理訊息
                message = event['message']['text']
                print(f"Received message: {message}")  # 打印接收到的消息
                if message.startswith("手槍集合"):
                    try:
                        _, start_date_str, end_date_str = message.split(" ")
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                        # 查詢數據庫
                        query = {'message': {'$regex': '素材'}, 'timestamp': {'$gte': start_date, '$lte': end_date}}
                        results = messages_collection.aggregate([
                            {'$match': query},
                            {'$group': {'_id': '$sender', 'count': {'$sum': 1}}}
                        ])

                        response_message = "查詢結果：\n"
                        for result in results:
                            response_message += f"ID: {result['_id']} 次數: {result['count']}\n"

                        print(f"Sending reply message: {response_message}")  # 打印回應內容

                        # 確認 LINE API 成功初始化後再進行回應
                        if line_bot_api:
                            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_message))
                        else:
                            print("LINE Bot API 未初始化，無法發送回應")

                    except ValueError as ve:
                        print(f"Date parsing error: {ve}")
                        if line_bot_api:
                            line_bot_api.reply_message(reply_token, TextSendMessage(text="查詢指令格式錯誤，請使用：查詢素材 YYYY-MM-DD YYYY-MM-DD"))
                        else:
                            print("LINE Bot API 未初始化，無法發送回應")
                else:
                    # 處理 "素材" 相關訊息
                    if "素材" in message:
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        print(f"Received message: {message} at {timestamp}")
                        messages_collection.insert_one({'sender': event['source']['userId'], 'message': message, 'timestamp': timestamp})

        return jsonify({'status': 'ok'})

    except InvalidSignatureError:
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
