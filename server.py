from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import os
import datetime
import re

app = FastAPI()

# ---------- 1. 首页 ----------
@app.get("/")
def home():
    return {
        "message": "✅ CL Experiment Data Server is running.",
        "usage": {
            "POST /upload_csv": "Upload CSV data (requires JSON: {'participant_id': 'xxx', 'csv_data': '...csv content...'})",
            "GET /list_files": "List all uploaded CSV files",
            "GET /download_csv/{filename}": "Download a specific CSV file"
        }
    }

# ---------- 2. 上传数据 ----------
@app.post("/upload_csv")
async def upload_csv(request: Request):
    """
    接收前端上传的 JSON 数据：
    {
        "participant_id": "P001",
        "csv_data": "csv 文件的内容字符串"
    }
    并在服务器端保存为 data/P001_data.csv
    """
    try:
        data = await request.json()
        participant_id = data.get("participant_id", "unknown").strip()
        csv_content = data.get("csv_data", "")

        if not csv_content:
            raise HTTPException(status_code=400, detail="No CSV data provided.")

        # 参与者ID合法性校验（防止注入路径）
        if not re.match(r"^[A-Za-z0-9_\-]+$", participant_id):
            raise HTTPException(status_code=400, detail="Invalid participant_id format.")

        # 创建存储目录
        os.makedirs("data", exist_ok=True)

        # 生成文件名：例如 P001_data_20251109_154010.csv
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{participant_id}_data_{timestamp}.csv"
        filepath = os.path.join("data", filename)

        # 保存文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)

        return {"status": "ok", "filename": filename, "path": filepath}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ---------- 3. 列出所有文件 ----------
@app.get("/list_files")
def list_files():
    if not os.path.exists("data"):
        return {"files": []}
    files = sorted(os.listdir("data"))
    return {"files": files, "count": len(files)}

# ---------- 4. 下载指定文件 ----------
@app.get("/download_csv/{filename}")
def download_csv(filename: str):
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found.")
    # 仅允许下载 .csv 文件
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    return FileResponse(filepath, filename=filename, media_type="text/csv")

# ---------- 5. 健康检查 ----------
@app.get("/health")
def health_check():
    return {"status": "running", "time": datetime.datetime.now().isoformat()}
