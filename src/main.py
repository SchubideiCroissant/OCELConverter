from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import os
from backendplaceholder import convert_to_uppercase

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def homepage():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/uppercase")
async def handle_upload(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as input_tmp:
        input_path = input_tmp.name
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_tmp:
        output_path = output_tmp.name

    convert_to_uppercase(input_path, output_path)
    os.remove(input_path)
    return FileResponse(output_path, media_type="text/plain", filename="converted.txt")