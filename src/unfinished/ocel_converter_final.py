
import pandas as pd
import json

# CSV-Datei mit Events + Objektinformationen
csv_path = "input_with_object_data.csv"
df = pd.read_csv(csv_path, encoding="utf-8-sig")

def convert_to_ocel2_export_format(df):
    ocel = {
        "objectTypes": [],
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

    # Objekt-Typen dynamisch sammeln
    object_types = df["object_type"].dropna().unique()
    for obj_type in object_types:
        ocel["objectTypes"].append({
            "name": obj_type,
            "attributes": []
        })

    # Objekte erfassen
    seen_objects = set()
    for _, row in df.dropna(subset=["caseid"]).iterrows():
        caseid = str(row["caseid"])
        if caseid in seen_objects:
            continue
        seen_objects.add(caseid)

        obj_type = row.get("object_type", "Vorgang")

        try:
            raw_attributes = row.get("object_attributes", "{}")
            parsed_attr = json.loads(raw_attributes.replace("'", '"'))
            attributes = [{"name": k, "value": v} for k, v in parsed_attr.items()]
        except Exception:
            attributes = []

        try:
            raw_relationships = row.get("object_relationships", "[]")
            relationships = json.loads(raw_relationships.replace("'", '"'))
        except Exception:
            relationships = []

        ocel["objects"].append({
            "id": caseid,
            "type": obj_type,
            "attributes": attributes,
            "relationships": relationships
        })

    # Events erfassen
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
                str(row.get("object_type", "Vorgang")): [str(row["caseid"])]
            }
        }
        ocel["events"].append(event)

    # Beispielrelationen aus caseid-Folgen erzeugen
    unique_caseids = list(df["caseid"].dropna().unique())
    for i in range(len(unique_caseids) - 1):
        ocel["ocel:relations"].append({
            "ocel:source": unique_caseids[i],
            "ocel:target": unique_caseids[i + 1],
            "ocel:relation_type": "example_relation"
        })

    return ocel

# Hilfsfunktion: konvertiert alles in JSON-kompatible Typen
def convert_json_compatible(obj):
    if isinstance(obj, dict):
        return {k: convert_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_json_compatible(i) for i in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    else:
        return obj

# Umwandlung starten
ocel2_data = convert_to_ocel2_export_format(df)
ocel2_data_clean = convert_json_compatible(ocel2_data)

# Datei speichern
output_file = "converted_ocel2_export.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(ocel2_data_clean, f, indent=2)

print(f"OCEL-Datei erfolgreich erzeugt: {output_file}")
