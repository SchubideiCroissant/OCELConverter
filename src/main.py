from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import tempfile
import os
from backendplaceholder import convert_to_uppercase

app = FastAPI()

@app.post("/uppercase")
async def handle_upload(file: UploadFile = File(...)):
    # Temporäre Dateien für Eingabe und Ausgabe
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as input_tmp:
        input_path = input_tmp.name
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_tmp:
        output_path = output_tmp.name

    # Umwandlung durchführen
    convert_to_uppercase(input_path, output_path)

    # Optional: Eingabedatei löschen
    os.remove(input_path)

    # Rückgabe der konvertierten Datei
    return FileResponse(output_path, media_type="text/plain", filename="converted.txt")


