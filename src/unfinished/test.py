import pandas as pd
import json

# CSV-Datei mit Events + Relationen
csv_path = "input.csv"
df = pd.read_csv(csv_path)

def convert_to_ocel2_export_format(df):
    ocel = {
        "objectTypes": [
            {
                "name": "Vorgang",
                "attributes": []
            }
        ],
        "eventTypes": [],
        "objects": [],
        "events": [],
        "ocel:relations": []
    }

    # EventTypes sammeln
    event_activities = df["activity"].dropna().unique()
    for activity in event_activities:
        ocel["eventTypes"].append({
            "name": activity,
            "attributes": ["processtype", "resource"]
        })

    # Objekte (caseid)
    seen_objects = set()
    for _, row in df.dropna(subset=["caseid"]).iterrows():
        caseid = str(row["caseid"])
        if caseid not in seen_objects:
            seen_objects.add(caseid)
            ocel["objects"].append({
                "id": caseid,
                "type": "Vorgang",
                "attributes": [],
                "relationships": []
            })

    # Events erfassen (wenn eventid vorhanden ist)
    for _, row in df.dropna(subset=["eventid"]).iterrows():
        attributes = []
        if pd.notna(row.get("processtype", None)):
            attributes.append({"name": "processtype", "value": row["processtype"]})
        if pd.notna(row.get("resource", None)):
            attributes.append({"name": "resource", "value": row["resource"]})

        event = {
            "id": row["eventid"],
            "activity": row["activity"],
            "timestamp": row["completiontime"],
            "attributes": attributes,
            "ocel:relations": {
                "Vorgang": [str(row["caseid"])]
            }
        }
        ocel["events"].append(event)

    # Relationen (wenn source+target+relation_type vorhanden)
    if {"source", "target", "relation_type"}.issubset(df.columns):
        for _, row in df.dropna(subset=["source", "target", "relation_type"]).iterrows():
            relation = {
                "ocel:source": str(row["source"]),
                "ocel:target": str(row["target"]),
                "ocel:relation_type": row["relation_type"]
            }
            ocel["ocel:relations"].append(relation)

    return ocel

# Konvertieren und speichern
ocel2_data = convert_to_ocel2_export_format(df)
output_path = "converted_ocel2_export.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(ocel2_data, f, indent=2)

print(f"OCEL-Datei erfolgreich gespeichert unter: {output_path}")
