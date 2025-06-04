import csv
import json
from typing import List, Dict, Tuple, Set
from datetime import datetime

# Mapping Data
mapping_data = {}

renaming_map = {}

def set_renaming(mapping: Dict[str, Dict[str, str]]):
    global renaming_map
    renaming_map = mapping

def apply_renaming(column: str, value: str) -> str:
    return renaming_map.get(column, {}).get(value, value)

# Funktion zum Setzen des Mappings
def set_mapping(mapping: Dict[str, list]):
    global mapping_data
    new_mapping = {}
    for obj_type, ids in mapping.items():
        renamed_ids = [apply_renaming("resource", str(i)) for i in ids]  
        new_mapping[obj_type] = renamed_ids
    mapping_data = new_mapping


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
    unique_ids = set()

    for row in event_list:
        evt_id = row["eventid"]

        # Überprüfung auf eindeutige eventID
        if evt_id in unique_ids:
            raise ValueError(f"Doppelte eventID gefunden: {evt_id}")
        unique_ids.add(evt_id)

        evt_type = row["activity"]
        evt_time = row["completiontime"]

        event_types.add(evt_type)

        relationships = []

        # Mapping Objects
        for obj_type, ids in mapping_data.items():
            for obj_id in ids:
                if obj_id in [apply_renaming("resource", v.strip()) for v in row.values()]:
                    obj_key = f"{obj_type}_{obj_id}"
                    if obj_key not in objects_output:
                        objects_output[obj_key] = {
                            "id": obj_key,
                            "type": obj_type,
                            "attributes": [],
                            "relationships": []
                        }
                    relationships.append({"objectId": obj_key, "qualifier": obj_type})
                    object_types.add(obj_type)  

        # Case Object
        case_id = row.get("caseid", "").strip()
        if case_id:
            case_key = case_id
            if case_key not in objects_output:
                objects_output[case_key] = {
                    "id": case_key,
                    "type": "Case",
                    "attributes": [],
                    "relationships": []
                }
            relationships.append({"objectId": case_key, "qualifier": "case"})
            object_types.add("Case")

        # Resource Object
        res_id = apply_renaming("resource", row.get("resource", "").strip())
        if res_id:
            res_key = f"res_{res_id}"
            if res_key not in objects_output:
                objects_output[res_key] = {
                    "id": res_key,
                    "type": "Resource",
                    "attributes": [],
                    "relationships": []
                }
            relationships.append({"objectId": res_key, "qualifier": "resource"})
            object_types.add("Resource")

        # Event-Eintrag
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

