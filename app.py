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

        return jsonify({'status': 'ok'})

# 新增查詢路由
@app.route("/search", methods=['GET'])
def search():
    keyword = "素材"  # 固定查詢關鍵字為 "素材"
    start_date_str = request.args.get('start_date')  # 接收查詢的開始日期
    end_date_str = request.args.get('end_date')      # 接收查詢的結束日期
    
    # 解析日期字串為 datetime 格式
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # 查詢特定日期範圍內提到 "素材" 的訊息
    query = {
        'message': {'$regex': keyword},
        'timestamp': {'$gte': start_date, '$lte': end_date}
    }
    
    # 使用 MongoDB 聚合統計每個發送者提到 "素材" 的次數
    results = messages_collection.aggregate([
        {'$match': query},
        {'$group': {'_id': '$sender', 'count': {'$sum': 1}}}
    ])

    # 返回結果
    return jsonify(list(results))

# 運行應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # 使用 Heroku 提供的端口
    app.run(host='0.0.0.0', port=port)
