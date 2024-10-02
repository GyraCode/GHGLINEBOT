from flask import Flask, request, jsonify
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

# 創建資料庫並儲存訊息
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  message TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

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
            
            conn = sqlite3.connect('messages.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)", (sender, message, timestamp))
            conn.commit()
            conn.close()
    
    return jsonify({'status': 'ok'})

# 根據關鍵字和時間範圍查詢訊息
@app.route("/search", methods=['GET'])
def search():
    keyword = request.args.get('keyword')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''SELECT sender, COUNT(*) FROM messages
                 WHERE message LIKE ? AND timestamp BETWEEN ? AND ?
                 GROUP BY sender''', ('%' + keyword + '%', start_date, end_date))
    results = c.fetchall()
    conn.close()
    
    return jsonify(results)

if __name__ == "__main__":
    init_db()
    app.run(port=5000)
