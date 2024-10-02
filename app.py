from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
import os
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

#line token
channel_access_token = '0T7Bd7/DpIKjDwfBFvNF/ucpM/3DFZw9rkpICfgcfm8IF30IC6hORpRBkdAu4KeLiGkhmpf6CJMvc+ydnP5fyjklBTJHvUOgSBMMR6OGM1XG1dlX2xQ+iVrq7sv00yDOKlCgZSUV7phm6KuGNQI4wAdB04t89/1O/w1cDnyilFU='
channel_secret = '433188037dc29d89488d1c0f2bcf1ea5'
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
app = Flask(__name__)

# 設置 MongoDB 連接
client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['Cluster0']  # 選擇數據庫名稱
messages_collection = db['messages']  # 選擇集合名稱（相當於 SQL 的表）

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

        
                # 檢查是否是查詢指令 (例如 "查詢素材 2023-09-01 2023-10-30")
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
                            {'$group': {'_id': '$sender', 'count': {'$sum': 1}}}  # 匯總每個 sender 的消息數
                        ])

                        # 構建查詢結果
                        response_message = "查詢結果：\n"
                        for result in results:
                            sender_id = result['_id']  # 獲取 sender 的 ID
                            try:
                                # 根據 sender_id 查詢用戶名稱
                                profile = line_bot_api.get_profile(sender_id)
                                sender_name = profile.display_name  # 用戶的顯示名稱
                            except LineBotApiError:
                                sender_name = "未知用戶"  # 如果無法獲取用戶名稱，使用默認名稱

                            # 將查詢結果構建為回應消息
                            response_message += f"名稱: {sender_name} 次數: {result['count']}\n"

                        # 回應群組內的查詢結果
                        reply_message(sender, response_message)




                    except ValueError:
                        reply_message(sender, "查詢指令格式錯誤，請使用：手槍集合 YYYY-MM-DD YYYY-MM-DD")
                else:
                    # 只在訊息包含 "素材" 關鍵字時才寫入資料庫
                   if "素材" in message:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)

                    # 打印接收到的訊息和發送者
                    print(f"Received message: {message} from {sender_name} at {timestamp}")
                    
                    # 插入到 MongoDB 中
                    messages_collection.insert_one({
                        'sender': sender_name,  # 存儲用戶名稱
                        'message': message,
                        'timestamp': timestamp
                    })
                    
                    # 查詢該用戶總共發送 "素材" 關鍵字的次數
                    total_count = messages_collection.count_documents({
                        'sender': sender_name,
                        'message': {'$regex': '素材'}
                    })

                    # 構建回應訊息
                    response_message = f"回報成功！名稱: {sender_name} 目前次數：{total_count} 次"
                    
                    # 回應群組內的結果
                    reply_message(sender, response_message)


                    return jsonify({'status': 'ok'})

# 回應訊息的函數
from linebot.models import TextSendMessage

def reply_message(to, message):
    try:
        # 使用 LINE Messaging API 發送消息
        line_bot_api.push_message(to, TextSendMessage(text=message))
        print(f"Replying to {to} with message: {message}")
    except LineBotApiError as e:
        print(f"LineBotApiError: {e}")


# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
    app.run(host='0.0.0.0', port=port)
