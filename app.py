from flask import Flask, request, jsonify
from pymongo import MongoClient
import threading
import requests
import json
import os
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
from datetime import datetime

# line token
channel_access_token = '0T7Bd7/DpIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XG1dlX2xQ+iVrq7sv00yDOKlCgZSUV7phm6KuGNQI4wAdB04t89/1O/w1cDnyilFU='
channel_secret = '433188037dc29d89488d1c0f2bcf1ea5'
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
app = Flask(__name__)

# 設置 MongoDB 連接
client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['Cluster0']  # 選擇數據庫名稱
messages_collection = db['messages']  # 選擇集合名稱（相當於 SQL 的表）

def ping_self():
    print("Ping function is running")  # 加入日誌來確認函數執行
    try:
        # 使用 GET 方法
        response = requests.get('https://app-nameless-pine-7492.fly.dev/webhook')
        print(f"Ping successful, status code: {response.status_code}")
    except Exception as e:
        print(f"Ping failed: {e}")
    
    # 每隔 1 分鐘 Ping 一次
    threading.Timer(500, ping_self).start()  # 每 1 分鐘


# Webhook 路由
@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "Webhook endpoint is working", 200
    
    if request.method == 'POST':
        body = request.get_data(as_text=True)
        data = json.loads(body)
        
        # 解析訊息並儲存到資料庫
        for event in data['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                
                # 判斷訊息來自群組、聊天室還是單一用戶
                if 'groupId' in event['source']:
                    sender = event['source']['groupId']  # 來自群組的消息
                    user_id = event['source']['userId']  # 獲取用戶的 userId
                    try:
                        # 使用 get_group_member_profile 獲取群組內的用戶名稱
                        profile = line_bot_api.get_group_member_profile(sender, user_id)
                        sender_name = profile.display_name  # 用戶的顯示名稱
                    except LineBotApiError as e:
                        sender_name = "未知群組用戶"  # 如果獲取失敗，使用默認名稱
                        print(f"無法獲取群組用戶名稱: {e}")
                elif 'roomId' in event['source']:
                    sender = event['source']['roomId']  # 來自聊天室的消息
                else:
                    sender = event['source']['userId']  # 來自單一用戶的消息

                message = event['message']['text']

                # 檢查是否是查詢指令
                if message.startswith("手槍集合"):
                    try:
                        _, start_date_str, end_date_str = message.split(" ")
                        
                        # 解析日期
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        
                        # 查詢數據庫中符合條件的消息
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
                            response_message += f"名稱: {result['_id']} 次數: {result['count']}\n"
                        
                        # 回應群組內的查詢結果
                        reply_message(sender, response_message)

                    except ValueError:
                        reply_message(sender, "查詢指令格式錯誤，請使用：手槍集合 YYYY-MM-DD YYYY-MM-DD")
                elif "素材" in message:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    
                    # 插入到 MongoDB 中
                    messages_collection.insert_one({
                        'sender': sender_name,  # 存儲用戶名稱
                        'message': message,
                        'timestamp': timestamp
                    })

                else:
                    # 心跳測試信息
                    print("心跳測試OK 跳動成功!")
                  
                return jsonify({'status': 'ok'})

# 回應訊息的函數
from linebot.models import TextSendMessage

def reply_message(to, message):
    try:
        line_bot_api.push_message(to, TextSendMessage(text=message))
        print(f"Replying to {to} with message: {message}")
    except LineBotApiError as e:
        print(f"LineBotApiError: {e}")

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    ping_self()
    app.run(host='0.0.0.0', port=port)
