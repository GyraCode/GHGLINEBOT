from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# LINE Messaging API 的密鑰
LINE_CHANNEL_ACCESS_TOKEN = '0T7Bd7/DPIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XXG114xQQpV 4t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 設置 MongoDB 連接
client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['Cluster0']
messages_collection = db['messages']

# Webhook 路由
@app.route("/webhook", methods=['POST'])
def webhook():
    try:
        body = request.get_data(as_text=True)
        data = json.loads(body)

        for event in data['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                # 提取 replyToken
                if 'replyToken' in event:
                    reply_token = event['replyToken']
                else:
                    print("No replyToken found")
                    continue

                # 處理訊息
                message = event['message']['text']
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

                        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_message))

                    except ValueError as ve:
                        print(f"Date parsing error: {ve}")
                        line_bot_api.reply_message(reply_token, TextSendMessage(text="查詢指令格式錯誤，請使用：查詢素材 YYYY-MM-DD YYYY-MM-DD"))
                else:
                    # 處理 "素材" 相關訊息
                    if "素材" in message:
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        print(f"Received message: {message} at {timestamp}")
                        messages_collection.insert_one({'sender': event['source']['userId'], 'message': message, 'timestamp': timestamp})

        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
