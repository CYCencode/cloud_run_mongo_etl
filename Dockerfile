# Dockerfile
# 使用官方 Python 基礎映像檔，推薦 slim 版本以減少體積
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /usr/src/app

# 將需求文件複製到工作目錄
COPY requirements.txt ./

# 安裝依賴項
# 使用 --no-cache-dir 確保映像檔大小最小化
RUN pip install --no-cache-dir -r requirements.txt

# 將應用程式碼複製到工作目錄
COPY . .

# 定義容器啟動時執行的命令
# Cloud Run 啟動容器後會執行此命令
CMD ["python", "main.py"]
