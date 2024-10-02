from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
from datetime import datetime

app = Flask(__name__)

# 設置 MongoDB 連接
client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['Cluster0']  # 選擇數據庫名稱
messages_collection = db['messages']  # 選擇集合名稱（相當於 SQL 的表）

# Webhook 路由
@app.route("/webhook", methods=['POST'])
def webhook():
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

# 根據關鍵字和時間範圍查詢訊息
@app.route("/search", methods=['GET'])
def search():
    keyword = request.args.get('keyword')
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    
    query = {
        'message': {'$regex': keyword},  # 模糊查詢
        'timestamp': {'$gte': start_date, '$lte': end_date}  # 範圍查詢
    }

    # 查詢 MongoDB
    results = messages_collection.aggregate([
        {'$match': query},
        {'$group': {'_id': '$sender', 'count': {'$sum': 1}}}
    ])

    # 返回查詢結果
    return jsonify(list(results))

if __name__ == "__main__":
    app.run(port=5000)
