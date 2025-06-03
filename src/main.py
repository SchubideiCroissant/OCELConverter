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
                max-width: 700px;
                margin-top: 50px;
                padding: 30px;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .btn {
                width: 100%;
                margin-top: 10px;
            }
            textarea {
                font-family: monospace;
                white-space: pre;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">CSV zu OCEL 2.0 Konverter</h2>

            <!-- Mapping JSON -->
            <form id="mappingForm">
                <h5>1. Mapping JSON eingeben</h5>
                <textarea id="mappingInput" class="form-control" rows="6" placeholder='{\n "Mitarbeiter": ["182", "19", "16", "1", "189"],\n "Teamleiter": ["53", "463"]\n}' required></textarea>
                <button type="submit" class="btn btn-secondary">Mapping senden</button>
                <div id="mappingResult" class="mt-2 text-success"></div>
            </form>

            <hr>

            <!-- CSV Upload -->
            <form id="uploadForm">
                <h5>2. CSV-Datei hochladen</h5>
                <input type="file" class="form-control" id="uploadFile" accept=".csv" required>
                <button type="submit" class="btn btn-primary">Datei hochladen &amp; verarbeiten</button>
                <div id="uploadResult" class="mt-2 text-success"></div>
            </form>

            <hr>

            <!-- Downloads -->
            <h5>3. Ergebnisse herunterladen</h5>
            <a href="/download/output" class="btn btn-outline-success" download>Output JSON herunterladen</a>
            <a href="/download/log" class="btn btn-outline-dark" download>Log-Datei herunterladen</a>
            <hr>

            <!-- Link zum GitHub-Repo -->
            <div class="text-center mt-3">
                <a href="https://github.com/SchubideiCroissant/OCELConverter" class="link-secondary" target="_blank">
                    GitHub-Repository dieses Projekts
                </a>
            </div>
            <!-- Ocelot -->
            <div class="text-center mt-3">
                <a href="https://ocelot.pm/" class="link-secondary" target="_blank">
                    Testen des Outputs hier
                </a>
            </div>

        </div>

        <!-- JavaScript -->
        <script>
            // Mapping senden
            document.getElementById("mappingForm").addEventListener("submit", async function(e) {
                e.preventDefault();
                const input = document.getElementById("mappingInput").value;
                try {
                    const response = await fetch("/mapping", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: input
                    });
                    const result = await response.json();
                    document.getElementById("mappingResult").innerText = "✅ Mapping gesendet.";
                } catch (err) {
                    document.getElementById("mappingResult").innerText = "❌ Fehler beim Senden.";
                }
            });

            // Datei hochladen
            document.getElementById("uploadForm").addEventListener("submit", async function(e) {
                e.preventDefault();
                const fileInput = document.getElementById("uploadFile");
                if (!fileInput.files.length) {
                    document.getElementById("uploadResult").innerText = "❌ Keine Datei ausgewählt.";
                    return;
                }

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                try {
                    const response = await fetch("/upload", {
                        method: "POST",
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error("Fehler beim Hochladen.");
                    }

                    const result = await response.json();
                    document.getElementById("uploadResult").innerText = "✅ Datei verarbeitet. Du kannst jetzt die Ergebnisse herunterladen.";
                } catch (err) {
                    document.getElementById("uploadResult").innerText = "❌ Fehler beim Hochladen.";
                }
            });
        </script>
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
        # Mapping setzen
        Converter.set_mapping(mapping_data)

        # Verarbeitung der CSV-Daten
        event_list = Converter.read_events_from_csv(input_path)
        events_output, objects_output, event_types, object_types = Converter.extract_events_and_objects(event_list)
        ocel_json = Converter.build_ocel_json_structure(events_output, objects_output, event_types, object_types)

        # Schreiben der JSON + Logdatei via Konverter
        Converter.write_output_files(ocel_json, log_path, output_path)

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

