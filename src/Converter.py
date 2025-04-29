import csv
import json
from typing import List, Dict, Tuple, Set


def read_events_from_csv(file_path: str) -> List[Dict]:
    events = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            events.append(row)
    return events


def extract_events_and_objects(event_list: List[Dict]) -> Tuple[List[Dict], Dict[str, Dict], Set[str], Set[str]]:
    event_types = set()
    object_types = set()
    events_output = []
    objects_output = {}

    for row in event_list:
        evt_id = row["eventid"]
        evt_type = row["activity"]
        evt_time = row["completiontime"]

        event_types.add(evt_type)

        relationships = []

        # Case Object
        case_id = row["caseid"]
        case_type = row["processtype"] or "Case"
        object_types.add(case_type)
        if case_id not in objects_output:
            objects_output[case_id] = {
                "id": case_id,
                "type": case_type,
                "attributes": [],
                "relationships": []
            }
        relationships.append({"objectId": case_id, "qualifier": "case"})

        # Resource Object
        res_id = row.get("resource")
        if res_id:
            res_type = "Resource"
            object_types.add(res_type)
            obj_id_res = f"res_{res_id}"
            if obj_id_res not in objects_output:
                objects_output[obj_id_res] = {
                    "id": obj_id_res,
                    "type": res_type,
                    "attributes": [],
                    "relationships": []
                }
            relationships.append({"objectId": obj_id_res, "qualifier": "resource"})

        event_entry = {
            "id": evt_id,
            "type": evt_type,
            "time": evt_time,
            "attributes": [],
            "relationships": relationships
        }
        events_output.append(event_entry)

    return events_output, objects_output, event_types, object_types


def build_ocel_json_structure(events_output: List[Dict], objects_output: Dict[str, Dict],
                              event_types: Set[str], object_types: Set[str]) -> Dict:
    event_types_list = [{"name": et, "attributes": []} for et in sorted(event_types)]
    object_types_list = [{"name": ot, "attributes": []} for ot in sorted(object_types)]

    return {
        "eventTypes": event_types_list,
        "objectTypes": object_types_list,
        "events": events_output,
        "objects": list(objects_output.values())
    }


def write_output_files(ocel_data: Dict, log_path: str, json_path: str) -> None:
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(ocel_data, jf, ensure_ascii=False, indent=2)

    total_events = len(ocel_data["events"])
    total_objects = len(ocel_data["objects"])
    total_event_types = len(ocel_data["eventTypes"])
    total_object_types = len(ocel_data["objectTypes"])
    event_object_rels = sum(len(evt["relationships"]) for evt in ocel_data["events"])
    object_object_rels = sum(len(obj.get("relationships", [])) for obj in ocel_data["objects"])

    with open(log_path, 'w', encoding='utf-8') as lf:
        lf.write(f"Konvertierte Events: {total_events}\n")
        lf.write(f"Konvertierte Objekte: {total_objects}\n")
        lf.write(f"Event-Typen (distinct): {total_event_types} - {', '.join([et['name'] for et in ocel_data['eventTypes']])}\n")
        lf.write(f"Objekt-Typen (distinct): {total_object_types} - {', '.join([ot['name'] for ot in ocel_data['objectTypes']])}\n")
        lf.write(f"Event-Objekt-Beziehungen: {event_object_rels}\n")
        lf.write(f"Objekt-Objekt-Beziehungen: {object_object_rels}\n")


# === Main Routine ===

csv_file = r"C:\Users\vince\PycharmProjects\OCELConverter\input\input.csv"
json_output_path = r"C:\Users\vince\PycharmProjects\OCELConverter\output\events_ocel.json"
log_output_path = r"C:\Users\vince\PycharmProjects\OCELConverter\output\conversion_log.txt"


event_list = read_events_from_csv(csv_file)
events_output, objects_output, event_types, object_types = extract_events_and_objects(event_list)
ocel_json = build_ocel_json_structure(events_output, objects_output, event_types, object_types)
write_output_files(ocel_json, log_output_path, json_output_path)

print("OCEL-JSON Datei und Log-Datei wurden erfolgreich erstellt.")
