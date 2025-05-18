from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import tempfile
import os
import json
from typing import Dict
import Converter

app = FastAPI()

# Output-Verzeichnis festlegen
output_dir = os.path.join(os.getcwd(), "output")
os.makedirs(output_dir, exist_ok=True)

# ===========================================
# Mapping-Daten
# ===========================================

# Globales Mapping-Dictionary
mapping_data = {}

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """
    Startseite mit Bootstrap Styling.
    """
    return """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>CSV zu OCEL 2.0 Konverter</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #f8f9fa;
            }
            .container {
                max-width: 600px;
                margin-top: 100px;
                padding: 30px;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .btn-primary {
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">CSV zu OCEL 2.0 Konverter</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="mb-3">
                    <input type="file" class="form-control" name="file" accept=".csv" required>
                </div>
                <button type="submit" class="btn btn-primary">Datei hochladen und verarbeiten</button>
            </form>

            <div class="mt-4">
                <h5>Weitere Endpoints:</h5>
                <ul>
                    <li><a href="/docs" class="link-primary">API Dokumentation (Swagger UI)</a></li>
                    <li><a href="/download/output" class="link-primary">Download output.json</a></li>
                    <li><a href="/download/log" class="link-primary">Download log.txt</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

# ===========================================
# Mapping Endpoints
# ===========================================

@app.post("/mapping")
async def set_mapping(mapping: Dict[str, list | str]):
    """
    Aktualisiere das Mapping. Unterstützt sowohl Einzelwert- als auch Listen-Mapping.
    """
    global mapping_data

    for key, value in mapping.items():
        if isinstance(value, str):
            mapping_data[key] = [value]
        elif isinstance(value, list):
            mapping_data[key] = value
        else:
            raise HTTPException(status_code=400, detail="Ungültiges Format. Nur str oder list erlaubt.")

    return {"message": "Mapping erfolgreich aktualisiert.", "mapping": mapping_data}

@app.get("/mapping")
async def get_mapping():
    """
    Gibt das aktuelle Mapping zurück.
    """
    return {"mapping": mapping_data}

# ===========================================
# Datei Upload Endpoint
# ===========================================

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    output_path = os.path.join(output_dir, "output.json")
    log_path = os.path.join(output_dir, "log.txt")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as input_tmp:
        input_path = input_tmp.name
        try:
            with open(input_path, "wb") as buffer:
                buffer.write(await file.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {str(e)}")

    try:
        # Mapping korrekt übergeben
        Converter.set_mapping(mapping_data)

        # Immer den echten Konverter benutzen
        ocel_json = process_with_converter(input_path)

        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(ocel_json, json_file, indent=2, ensure_ascii=False)

        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"Mapping verwendet: {bool(mapping_data)}\n")
            log_file.write(f"Mapping-Daten: {json.dumps(mapping_data, indent=2)}\n")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler bei der Verarbeitung: {str(e)}")
    finally:
        os.remove(input_path)

    return JSONResponse(content={
        "message": "Datei erfolgreich verarbeitet.",
        "output_path": output_path,
        "log_path": log_path
    })

# ===========================================
# Verarbeitungsfunktionen
# ===========================================

def process_with_mapping(mapping: dict) -> dict:
    """
    Verarbeitung basierend auf Mapping-Daten.
    """
    ocel_json = {"objects": []}
    for key, values in mapping.items():
        for value in values:
            ocel_json["objects"].append({"id": key, "resource": value})
    return ocel_json

def process_with_converter(input_path: str) -> dict:
    """
    Verarbeitung der CSV-Datei über den Converter.
    """
    event_list = Converter.read_events_from_csv(input_path)
    events_output, objects_output, event_types, object_types = Converter.extract_events_and_objects(event_list)
    ocel_json = Converter.build_ocel_json_structure(events_output, objects_output, event_types, object_types)
    return ocel_json

# ===========================================
# Download Endpoints
# ===========================================

@app.get("/download/output")
async def download_output():
    """ Download der output.json Datei """
    file_path = os.path.join(output_dir, "output.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json", filename="output.json")
    else:
        raise HTTPException(status_code=404, detail="Die output.json Datei wurde nicht gefunden.")

@app.get("/download/log")
async def download_log():
    """ Download der log.txt Datei """
    file_path = os.path.join(output_dir, "log.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/plain", filename="log.txt")
    else:
        raise HTTPException(status_code=404, detail="Die log.txt Datei wurde nicht gefunden.")

