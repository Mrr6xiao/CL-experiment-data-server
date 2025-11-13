from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import datetime
import re

app = FastAPI()

# ---------- CORS 允许前端脚本调用 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 首页：文件列表 + 下载 + 删除 ----------
@app.get("/", response_class=HTMLResponse)
def home():
    os.makedirs("data", exist_ok=True)
    files = sorted(os.listdir("data"))

    html = """
    <html>
    <head>
        <title>CL Experiment Data Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #fafafa; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 90%; margin-top: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; }
            tr:hover { background-color: #f1f1f1; }
            button {
                padding: 5px 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover { background-color: #45a049; }
            .delete-btn {
                background-color: #e74c3c;
                margin-left: 10px;
            }
            .delete-btn:hover {
                background-color: #c0392b;
            }
        </style>
        <script>
            async function deleteFile(filename) {
                if (!confirm('确定要删除文件: ' + filename + ' 吗？')) return;
                const res = await fetch('/delete_csv/' + filename, { method: 'DELETE' });
                const data = await res.json();
                if (data.status === 'ok') {
                    alert('✅ 已删除: ' + filename);
                    location.reload();
                } else {
                    alert('❌ 删除失败: ' + (data.detail || '未知错误'));
                }
            }
        </script>
    </head>
    <body>
        <h1>✅ CL Experiment Data Server</h1>
        <p>已上传的实验数据文件（点击下载或删除）</p>
        <table>
            <tr><th>文件名</th><th>操作</th></tr>
    """

    if files:
        for f in files:
            html += f"""
            <tr>
                <td>{f}</td>
                <td>
                    <a href="/download_csv/{f}" target="_blank">
                        <button>下载</button>
                    </a>
                    <button class="delete-btn" onclick="deleteFile('{f}')">删除</button>
                </td>
            </tr>
            """
    else:
        html += "<tr><td colspan='2'>暂无上传文件</td></tr>"

    html += """
        </table>
        <p style="margin-top:20px; font-size: 13px; color: #555;">
            📦 文件存储于 Render 云端 /data 目录<br>
            使用 POST /upload_csv 可上传实验数据。
        </p>
    </body>
    </html>
    """
    return html

# ---------- 上传接口 ----------
@app.post("/upload_csv")
async def upload_csv(request: Request):
    try:
        data = await request.json()
        participant_id = data.get("participant_id", "unknown").strip()
        csv_content = data.get("csv_data", "")

        if not csv_content:
            raise HTTPException(status_code=400, detail="No CSV data provided.")

        if not re.match(r"^[A-Za-z0-9_\-]+$", participant_id):
            raise HTTPException(status_code=400, detail="Invalid participant_id format.")

        os.makedirs("data", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{participant_id}_data_{timestamp}.csv"
        filepath = os.path.join("data", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)

        return {"status": "ok", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ---------- 文件下载 ----------
@app.get("/download_csv/{filename}")
def download_csv(filename: str):
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found.")
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    return FileResponse(filepath, filename=filename, media_type="text/csv")

# ---------- 文件删除 ----------
@app.delete("/delete_csv/{filename}")
def delete_csv(filename: str):
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"status": "error", "detail": "File not found."})

    try:
        os.remove(filepath)
        return {"status": "ok", "detail": f"Deleted {filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

# ---------- 文件列表 ----------
@app.get("/list_files")
def list_files():
    if not os.path.exists("data"):
        return {"files": []}
    files = sorted(os.listdir("data"))
    return {"files": files, "count": len(files)}

# ---------- 健康检查 ----------
@app.get("/health")
def health_check():
    return {"status": "running", "time": datetime.datetime.now().isoformat()}
