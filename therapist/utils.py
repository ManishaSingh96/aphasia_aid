import os , json ,re
def extract_json_from_response(response_str):
    """
    Cleans and extracts the first JSON object from the LLM output.
    """
    if not response_str or not isinstance(response_str, str):
        raise ValueError("Invalid or empty response string")

    try:
        cleaned = re.sub(r"^.*?[\{[]", "{", response_str.strip(), flags=re.DOTALL)
        cleaned = re.sub(r"[\}][^\}]*$", "}", cleaned.strip(), flags=re.DOTALL)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("⚠️ JSON Decode Error:", e)
        print("⚠️ Raw string was:", response_str)
        raise e

def safe_parse_json(text: str) -> dict:
        """
        Lenient JSON parser: tries json.loads first, then extracts first {...} block.
        """
        print(len(text), ' in safe oarser')
        try:
            return json.loads(text)
        except Exception:
            # fallback to first {...}
            import re
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                raise ValueError("No JSON object found in model output.")
            return json.loads(m.group(0))
        


def clean_json(text):
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
        print("match found")
    else:
        json_text=text
        print("No match found.")
    return json_text

from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

def _as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return {int(k): v for k, v in json.loads(value).items()}
    except Exception:
        return {}


