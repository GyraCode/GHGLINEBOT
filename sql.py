from pymongo import MongoClient

def get_mongo_client():
    try:
        client = MongoClient("mongodb+srv://x513465:1KdJi9XRKfysuTes@cluster0.ierkl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        db = client['Cluster0']  # 選擇數據庫名稱
        messages_collection = db['messages']  # 選擇集合名稱
        print("MongoDB 連接成功")
        return messages_collection
    except Exception as e:
        print(f"MongoDB 連接失敗: {e}")
        return None
