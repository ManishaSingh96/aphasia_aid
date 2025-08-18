import json

def load_kb(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_kb_by_persona(kb, persona):
    results = []
    for obj in kb.get("objects", []):
        match = True

        # Check severity / suitable_for
        if persona["severity"].lower() not in [s.lower() for s in obj.get("suitable_for", [])]:
            match = False

        # Lifestyle
        if persona["location"].lower() not in [l.lower() for l in obj.get("lifestyle", [])] and "both" not in [l.lower() for l in obj.get("lifestyle", [])]:
            match = False

        # Gender
        if persona["gender"].lower() not in [g.lower() for g in obj.get("gender", [])] and "all" not in [g.lower() for g in obj.get("gender", [])]:
            match = False

        # Profession
        if persona["profession"].lower() not in [p.lower() for p in obj.get("profession", [])] and "any" not in [p.lower() for p in obj.get("profession", [])]:
            match = False

        # City (if provided)
        if persona.get("city"):
            if persona["city"].lower() not in [c.lower() for c in obj.get("city_specific", [])] and obj.get("city_specific"):
                match = False

        if match:
            results.append(obj)
    return results


# Example usage
persona = {
    "profession": "teacher",
    "age": 70,
    "gender": "male",
    "location": "urban",
    "language": "hi-IN",
    "severity": "mild",
    "city": "bangalore"
}

kb = load_kb("aphasia_kb.json")
filtered_objects = filter_kb_by_persona(kb, persona)

print(f"Found {len(filtered_objects)} matching objects")
result={}
for obj in filtered_objects:
    result[obj["object_name_en"]]=obj["category"]
    # print(obj["object_name_en"], "-", obj["category"])
print(result)

