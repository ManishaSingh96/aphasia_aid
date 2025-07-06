import re
def clean_json(text):
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
        print("match found")
    else:
        json_text=text
        print("No match found.")
    return json_text
