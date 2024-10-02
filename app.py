from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from sql import get_mongo_client  # 從 sql.py 引入 MongoDB 連接

app = Flask(__name__)

# 初始化 MongoDB 連接
messages_collection = get_mongo_client()

# 設置 LINE Messaging API 的密鑰和 SECRET
LINE_CHANNEL_ACCESS_TOKEN = '0T7Bd7/DpIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XG1dlX2xQ+iVrq7sv00yDOKlCgZSUV7phm6KuGNQI4wAdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '433188037dc29d89488d1c0f2bcf1ea5'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/webhook", methods=['POST'])
def webhook():
    # 獲取簽名來自請求的 headers
    signature = request.headers.get('X-Line-Signature')

    # 獲取請求主體
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
            # 判斷訊息來自群組、聊天室還是單一用戶
            if 'groupId' in event['source']:
                sender = event['source']['groupId']  # 來自群組的消息
            elif 'roomId' in event['source']:
                sender = event['source']['roomId']  # 來自聊天室的消息
            else:
                sender = event['source']['userId']  # 來自單一用戶的消息

            message = event['message']['text']

            # 處理查詢指令
            if message.startswith("查詢素材"):
                try:
                    _, start_date_str, end_date_str = message.split(" ")
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                    # 查詢數據庫
                    query = {
                        'message': {'$regex': '素材'},
                        'timestamp': {'$gte': start_date, '$lte': end_date}
                    }
                    results = messages_collection.aggregate([
                        {'$match': query},
                        {'$group': {'_id': '$sender', 'count': {'$sum': 1}}}
                    ])

                    # 構建查詢結果
                    response_message = "查詢結果：\n"
                    for result in results:
                        response_message += f"ID: {result['_id']} 次數: {result['count']}\n"

                    # 回應查詢結果
                    reply_message(sender, response_message)

                except ValueError:
                    reply_message(sender, "查詢指令格式錯誤，請使用：查詢素材 YYYY-MM-DD YYYY-MM-DD")
            else:
                # 如果訊息包含 "素材"，儲存到資料庫
                if "素材" in message:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    print(f"Received message: {message} from {sender} at {timestamp}")

                    # 儲存到 MongoDB
                    messages_collection.insert_one({
                        'sender': sender,
                        'message': message,
                        'timestamp': timestamp
                    })

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
