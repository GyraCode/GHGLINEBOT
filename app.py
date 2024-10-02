from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime
import os

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
                sender = event['source']['userId']
                message = event['message']['text']
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)

                # 打印接收到的訊息和發送者
                print(f"Received message: {message} from {sender} at {timestamp}")
                
                # 插入到 MongoDB 中
                messages_collection.insert_one({
                    'sender': sender,
                    'message': message,
                    'timestamp': timestamp
                })

        return jsonify({'status': 'ok'})

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
    app.run(host='0.0.0.0', port=port)
