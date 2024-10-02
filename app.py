from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
import os
from linebot import LineBotApi, WebhookHandler

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
                elif 'roomId' in event['source']:
                    sender = event['source']['roomId']  # 來自聊天室的消息
                else:
                    sender = event['source']['userId']  # 來自單一用戶的消息

                message = event['message']['text']

                 # 只在訊息包含 "素材" 關鍵字時才寫入資料庫
                if "素材" in message:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)

                    # 打印接收到的訊息和發送者
                    print(f"Received message: {message} from {sender} at {timestamp}")
                    
                    # 插入到 MongoDB 中
                    messages_collection.insert_one({
                        'sender': sender,
                        'message': message,
                        'timestamp': timestamp
                    })

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
                            response_message += f"ID: {result['_id']} 次數: {result['count']}\n"
                        
                        
                        # 回應群組內的查詢結果
                        reply_message(sender, response_message)

                    except ValueError:
                        reply_message(sender, "查詢指令格式錯誤，請使用：查詢素材 YYYY-MM-DD YYYY-MM-DD")
             
                   

        return jsonify({'status': 'ok'})
    from linebot.models import TextMessage, TextSendMessage

# 處理 MessageEvent 事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text  # 獲取用戶發送的消息

    if '手槍集合' in msg:  # 如果消息中包含 "手槍集合"
        response_message = "收到 '手槍集合' 指令"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
    else:
        response_message = f"你剛剛說了: {msg}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))


# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
    app.run(host='0.0.0.0', port=port)