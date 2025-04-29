# Basis-Image: Python 3.11
FROM python:3.11-slim

# Arbeitsverzeichnis im Container erstellen
WORKDIR /app/src

# Lokale Dateien in das Arbeitsverzeichnis kopieren
COPY src/ .

# Notwendige Python-Bibliotheken installieren
RUN pip install pandas

# Befehl, der beim Starten des Containers ausgeführt wird
CMD ["python", "ocel_converter_final.py"]
