import json

# Objekte erfassen (mit Typ, Attributen, Beziehungen aus CSV)
seen_objects = set()

for _, row in df.dropna(subset=["caseid"]).iterrows():
    caseid = str(row["caseid"])
    if caseid in seen_objects:
        continue
    seen_objects.add(caseid)

    # Objekt-Typ: aus Spalte 'object_type', sonst Standard "Vorgang"
    obj_type = row.get("object_type", "Vorgang")

    # Attribute: JSON-String wie "{'bundesland': 'NRW'}"
    try:
        raw_attributes = row.get("object_attributes", "{}")
        parsed_attr = json.loads(raw_attributes.replace("'", '"'))  # einfache in doppelte Quotes
        attributes = [{"name": k, "value": v} for k, v in parsed_attr.items()]
    except Exception:
        attributes = []

    # Beziehungen: JSON-String wie "[{'type': 'verlinkt', 'target': '456'}]"
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
