from fastapi import FastAPI, Request
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
