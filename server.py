from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os, datetime

app = FastAPI()

@app.post("/upload_csv")
async def upload_csv(request: Request):
    csv_data = await request.body()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data", exist_ok=True)
    filename = f"data/participant_{timestamp}.csv"
    with open(filename, "wb") as f:
        f.write(csv_data)
    return {"status": "ok", "filename": filename}

# ✅ 新增接口：返回当前所有CSV文件名
@app.get("/list_files")
def list_files():
    files = os.listdir("data") if os.path.exists("data") else []
    return {"files": files}

# ✅ 新增接口：下载指定文件
@app.get("/download_csv/{filename}")
def download_csv(filename: str):
    filepath = f"data/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type='text/csv')
    else:
        return {"error": "file not found"}
