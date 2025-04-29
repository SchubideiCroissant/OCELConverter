# CSV to OCELConverter – Microservice

Dieses Projekt stellt einen Microservice bereit, der über eine Weboberfläche eine Datei entgegennimmt, verarbeitet und eine OEL 2.0 Datei ausliefert.


---

## Funktionen

- Upload einer `.csv`-Datei über eine Weboberfläche 
- Verarbeitung der Datei 
- Automatischer Download der verarbeiteten Datei

---

## Projektstruktur

```
OCELConverter/
├── Dockerfile               # Definiert den Docker-Container
├── requirements.txt         # Python-Abhängigkeiten
├── projektbericht.adoc      # Projektbeschreibung und Dokumentation
└── src/
    ├── main.py              # FastAPI-Microservice mit Datei-Upload
    ├── converter.py  # Modullogik für die Umwandlung
    └── static/
        └── index.html       # Weboberfläche zum Datei-Upload
```

## Dokumentation

Weitere Informationen finden sich im [Projektbericht](projektbericht.adoc).

## Installation und Ausführung mit Docker

**Voraussetzungen**  
Docker muss installiert sein

**Klonen des Projekts**  
`git clone https://github.com/SchubideiCroissant/OCELConverter.git`  
`cd OCELConverter`

**Docker-Image bauen**  
`docker build -t ocel-microservice .`

**Container starten**  
`docker run -p 8000:8000 ocel-microservice`


## Nutzung

**Weboberfläche**  
Öffne im Browser:

[http://localhost:8000/](http://localhost:8000/)

Hier kann eine `.csv`-Datei hochgeladen und verarbeitet werden.

Datei auswählen oder per Drag & Drop hineinziehen,  
dann auf **„Umwandeln“** klicken.


## Abhängigkeiten

Die notwendigen Python-Bibliotheken befinden sich in der Datei `requirements.txt`:

- `fastapi`
- `uvicorn`
- `python-multipart`

Diese werden beim Docker-Build automatisch installiert.


## Autoren

Dieses Projekt wurde erstellt von:

- **Arthur Mehlgarten ** – [@SchubideiCroissant](https://github.com/SchubideiCroissant)
- ** Anne Panzer ** – [@annedoesstuff](https://github.com/annedoesstuff)
- **Equal* – [@2ealqada](https://github.com/2ealqada)
- **Vincent Schick* – [@Qbito-3](https://github.com/2ealqada)


