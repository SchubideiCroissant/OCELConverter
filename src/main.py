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


@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
    <!DOCTYPE html>
    <html lang=\"de\">
    <head>
        <meta charset=\"UTF-8\">
        <title>CSV zu OCEL 2.0 Konverter</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
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
        <div class=\"container\">
            <h2 class=\"text-center mb-4\">CSV zu OCEL 2.0 Konverter</h2>

            <!-- Mapping JSON -->
            <form id=\"mappingForm\">
                <h5>1. Mapping JSON eingeben</h5>
                <textarea id=\"mappingInput\" class=\"form-control\" rows=\"6\" placeholder='{"Mitarbeiter": ["182", "19", "16", "1", "189"], "Teamleiter": ["53", "463"]}' required></textarea>
                <button type=\"submit\" class=\"btn btn-secondary\">Mapping senden</button>
                <div id=\"mappingResult\" class=\"mt-2 text-success\"></div>
            </form>

            <!-- Renaming JSON -->
            <form id=\"renamingForm\">
                <h5 class=\"mt-4\">Optional: Umbenennungs-Mapping</h5>
                <textarea id=\"renamingInput\" class=\"form-control\" rows=\"6\" placeholder='{"resource": {"182": "Max Mustermann", "19": "Lisa Beispiel"}}'></textarea>
                <button type=\"submit\" class=\"btn btn-secondary\">Renaming senden</button>
                <div id=\"renamingResult\" class=\"mt-2 text-success\"></div>
            </form>

            <hr>

            <!-- CSV Upload -->
            <form id=\"uploadForm\">
                <h5>2. CSV-Datei hochladen</h5>
                <input type=\"file\" class=\"form-control\" id=\"uploadFile\" accept=\".csv\" required>
                <button type=\"submit\" class=\"btn btn-primary\">Datei hochladen &amp; verarbeiten</button>
                <div id=\"uploadResult\" class=\"mt-2 text-success\"></div>
            </form>

            <button id="resetButton" class="btn btn-outline-danger mt-3">Mapping & Renaming zurücksetzen</button>
            <div id="resetResult" class="mt-2 text-success"></div>


            <hr>

            <!-- Downloads -->
            <h5>3. Ergebnisse herunterladen</h5>
            <a href=\"/download/output\" class=\"btn btn-outline-success\" download>Output JSON herunterladen</a>
            <a href=\"/download/log\" class=\"btn btn-outline-dark\" download>Log-Datei herunterladen</a>
            <hr>

            <!-- Link zum GitHub-Repo -->
            <div class=\"text-center mt-3\">
                <a href=\"https://github.com/SchubideiCroissant/OCELConverter\" class=\"link-secondary\" target=\"_blank\">
                    GitHub-Repository dieses Projekts
                </a>
            </div>
            <!-- Ocelot -->
            <div class=\"text-center mt-3\">
                <a href=\"https://ocelot.pm/\" class=\"link-secondary\" target=\"_blank\">
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

            document.getElementById("resetButton").addEventListener("click", async function () {
            try {
                const response = await fetch("/reset", { method: "POST" });
                const result = await response.json();
                document.getElementById("resetResult").innerText = "✅ Zurückgesetzt.";
                document.getElementById("mappingInput").value = "";
                document.getElementById("renamingInput").value = "";
            } catch (err) {
                document.getElementById("resetResult").innerText = "❌ Fehler beim Zurücksetzen.";
            }
        });


            // Renaming senden
            document.getElementById("renamingForm").addEventListener("submit", async function(e) {
                e.preventDefault();
                const input = document.getElementById("renamingInput").value;
                try {
                    const response = await fetch("/renaming", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: input
                    });
                    const result = await response.json();
                    document.getElementById("renamingResult").innerText = "✅ Renaming gesendet.";
                } catch (err) {
                    document.getElementById("renamingResult").innerText = "❌ Fehler beim Senden.";
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
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """


# ===========================================
# Mapping Endpoints
# ===========================================

@app.post("/renaming")
async def set_renaming(mapping: Dict[str, Dict[str, str]]):
    try:
        Converter.set_renaming(mapping)
        return {"message": "Renaming erfolgreich übernommen."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mapping")
async def set_mapping(mapping: Dict[str, list | str]):
    """
    Mapping an den Konverter weiterreichen.
    """
    converted_mapping = {}
    for key, value in mapping.items():
        converted_mapping[key] = [value] if isinstance(value, str) else value
    Converter.set_mapping(converted_mapping)
    return {"message": "Mapping erfolgreich aktualisiert.", "mapping": converted_mapping}


@app.get("/mapping")
async def get_mapping():
    return {"mapping": Converter.mapping_data}


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
# Download Endpoints
# ===========================================

@app.get("/download/output")
async def download_output():
    file_path = os.path.join(output_dir, "output.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json", filename="output.json")
    else:
        raise HTTPException(status_code=404, detail="Die output.json Datei wurde nicht gefunden.")


@app.get("/download/log")
async def download_log():
    file_path = os.path.join(output_dir, "log.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/plain", filename="log.txt")
    else:
        raise HTTPException(status_code=404, detail="Die log.txt Datei wurde nicht gefunden.")

@app.post("/reset")
async def reset_all():
    Converter.set_mapping({})
    Converter.set_renaming({})
    return {"message": "Mapping und Renaming wurden zurückgesetzt."}
