from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import os
import datetime
import re

app = FastAPI()

# ---------- 1. 首页：显示文件列表 + 下载按钮 ----------
@app.get("/", response_class=HTMLResponse)
def home():
    os.makedirs("data", exist_ok=True)
    files = sorted(os.listdir("data"))

    html = """
    <html>
        <head>
            <title>CL Experiment Data Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 80%; }
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
            </style>
        </head>
        <body>
            <h1>✅ CL Experiment Data Server</h1>
            <p>已上传的文件列表（点击下载）</p>
            <table>
                <tr><th>文件名</th><th>操作</th></tr>
    """

    if files:
        for f in files:
            html += f"""
                <tr>
                    <td>{f}</td>
                    <td>
                        <a href="/download_csv/{f}">
                            <button>下载</button>
                        </a>
                    </td>
                </tr>
            """
    else:
        html += "<tr><td colspan='2'>暂无上传文件</td></tr>"

    html += """
            </table>
            <p style="margin-top:20px; font-size: 13px; color: #555;">
            📦 所有数据存储于云端 Render 的 /data 目录。<br>
            你也可以通过 <code>/list_files</code> 或 <code>/download_csv/&lt;filename&gt;</code> 接口直接访问。
            </p>
        </body>
    </html>
    """
    return html

# ---------- 2. 上传数据 ----------
@app.post("/upload_csv")
async def upload_csv(request: Request):
    """
    接收前端上传的 JSON 数据：
    {
        "participant_id": "P001",
        "csv_data": "csv 文件的内容字符串"
    }
    并在服务器端保存为 data/P001_data_时间戳.csv
    """
    try:
        data = await request.json()
        participant_id = data.get("participant_id", "unknown").strip()
        csv_content = data.get("csv_data", "")

        if not csv_content:
            raise HTTPException(status_code=400, detail="No CSV data provided.")

        # ID格式校验
        if not re.match(r"^[A-Za-z0-9_\-]+$", participant_id):
            raise HTTPException(status_code=400, detail="Invalid participant_id format.")

        # 创建文件夹
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{participant_id}_data_{timestamp}.csv"
        filepath = os.path.join("data", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)

        return {"status": "ok", "filename": filename, "path": filepath}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ---------- 3. 下载接口 ----------
@app.get("/download_csv/{filename}")
def download_csv(filename: str):
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found.")
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    return FileResponse(filepath, filename=filename, media_type="text/csv")

# ---------- 4. 列出文件 JSON ----------
@app.get("/list_files")
def list_files():
    if not os.path.exists("data"):
        return {"files": []}
    files = sorted(os.listdir("data"))
    return {"files": files, "count": len(files)}

# ---------- 5. 健康检查 ----------
@app.get("/health")
def health_check():
    return {"status": "running", "time": datetime.datetime.now().isoformat()}
