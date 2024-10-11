# 使用 Python 的基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製所有代碼到容器中
COPY . /app

# 安裝 Flask 和其他所需的依賴
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口 8080，這是 Cloud Run 默認要求的端口
EXPOSE 8080

# 使用 CMD 來啟動 Flask 應用
CMD ["python", "app.py"]
