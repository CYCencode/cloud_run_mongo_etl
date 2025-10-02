# main.py
import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionError

# --- 日誌記錄函式 (Log to Mongo with Fallback) ---
def log_to_mongo(log_level: str, message: str, details=None):
    """
    從環境變數獲取 MongoDB 連線資訊，並將日誌寫入指定的 Collection。
    在連線失敗時，退回到標準輸出 (stderr) 進行緊急輸出。
    """
    MONGO_URI = os.environ.get("MONGO_URI")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "etl_monitoring")
    MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "pipeline_logs")
    
    # 獲取環境資訊，用於日誌追蹤
    AUTHOR_NAME = os.environ.get("AUTHOR_NAME", "unknown_author")
    # K_SERVICE 是 Cloud Run 自動注入的服務名稱
    CLOUD_RUN_SERVICE = os.environ.get("K_SERVICE", "local-run") 
    IMAGE_TAG = os.environ.get("IMAGE_TAG", "unknown_tag")
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc), 
        "level": log_level,
        "message": message,
        "pipeline_name": "real_estate_etl",  # 使用您的專案名稱
        "author": AUTHOR_NAME,
        "image_info": {
            "service": CLOUD_RUN_SERVICE, 
            "tag": IMAGE_TAG
        },
        "details": details if details is not None else {}
    }

    # 準備 fallback 訊息
    fallback_message = f"[{log_level}][{CLOUD_RUN_SERVICE}@{IMAGE_TAG}] {message}"
    if details:
        # 將詳細資訊也輸出到 stderr
        fallback_message += f" | Details: {details.get('error_message', 'N/A')}"
    
    if not MONGO_URI:
        # 如果 MONGO_URI 沒有設定，退回到標準錯誤輸出
        print(f"[Fallback Log - No URI] {fallback_message}", file=sys.stderr)
        return

    client = None
    try:
        # 使用 w=0 確保非同步寫入 (fire-and-forget)，減少延遲
        client = MongoClient(MONGO_URI, 
                             serverSelectionTimeoutMS=5000, 
                             w=0, 
                             connect=True) 
        db = client[MONGO_DB_NAME]
        db[MONGO_COLLECTION].insert_one(log_entry)
        
    except Exception as e:
        # 如果 MongoDB 寫入失敗，則退回到標準輸出進行緊急日誌記錄
        print(f"[MONGO_FAILOVER - {log_level}] {fallback_message} (Mongo Write Error: {e})", file=sys.stderr)
    finally:
        if client:
            client.close()


# --- MVP 連線驗證主流程 ---
def run_psc_mvp_test():
    """執行 PSC 連線驗證並寫入結果日誌"""
    MONGO_URI = os.environ.get("MONGO_URI")

    if not MONGO_URI:
        log_to_mongo("CRITICAL", "Test Aborted: MONGO_URI is missing.", 
                     details={"hint": "Set MONGO_URI environment variable."})
        sys.exit(1)

    client = None
    try:
        print("Attempting to connect to MongoDB Atlas via PSC...")
        
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            connect=True
        )

        # 執行 Ping 命令，驗證連線是否活躍
        client.admin.command('ping')
        
        # 連線成功時，使用 log_to_mongo 寫入成功日誌
        log_to_mongo("SUCCESS", "PSC Connection Test successful and verified.", 
                     details={"status": "MongoDB Ping successful"})
        
        print("==================================================")
        print("✅ SUCCESS: Connection verified and log written to MongoDB.")
        print("==================================================")
        sys.exit(0)

    except ConnectionError as e:
        # 連線失敗時，寫入 ERROR 日誌 (會觸發 fallback 到 stderr)
        log_to_mongo("ERROR", "PSC Connection Test FAILED", 
                     details={"error_message": f"Connection Error: {e}"})
        sys.exit(1)
    except Exception as e:
        # 其他錯誤
        log_to_mongo("CRITICAL", "An unexpected critical error occurred during test", 
                     details={"error_message": str(e)})
        sys.exit(1)
    finally:
        if client:
            client.close()

if __name__ == '__main__':
    run_psc_mvp_test()
