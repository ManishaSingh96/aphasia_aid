import os
import openai
import pandas as pd
import re
import json


class Image_Caption_Filter:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def clean_json(self, text: str) -> str:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
            print("match found")
        else:
            json_text = text.strip()
            print("No match found.")
        return json_text

    def _rule_based_fallback(self, object_name: str) -> dict:
        """Deterministic minimal captions for common objects; generic fallback otherwise."""
        obj = object_name.strip().lower()
        presets = {
            "apple": [
                "red apple with green leaf",
                "red apple with green stem",
                "red apple on white"
            ],
            "towel": [
                "towel in white",
                "white cotton towel",
                "bath towel on white"
            ],
            "soap": [
                "soap bar",
                "white soap bar",
                "soap bubbles"
            ],
            "eggs": [
                "eggs in a tray",
                "brown eggs in tray",
                "eggs on white"
            ],
            "egg": [
                "egg on white",
                "brown egg on white",
                "egg in egg cup"
            ]
        }
        items = presets.get(obj, [
            f"{object_name} on white",
            f"{object_name} close up",
            f"{object_name} centered on white"
        ])
        out = {}
        for i, cap in enumerate(items, 1):
            out[f"caption{i}"] = cap
        return out

    def generate_simple_prompts(self, object_name: str, max_captions: int = 5) -> dict:
        """
        Generate short, descriptive, flashcard-style captions for the given object.
        Returns a dict like {"caption1": "...", "caption2": "...", ...}
        """
        system_prompt = (
            "You generate ultra-short, descriptive captions for flashcard-style images. "
            "Captions must be simple noun/adjective phrases (no sentences), 3–7 words, "
            "single target object only, plain background implied, everyday Indian context. "
            "Avoid scenes, actions, multiple objects, rooms, brands, and quantities. "
            "Prefer the most common real-world variant/color for the object in India. "
            "Output JSON only, with keys caption1..captionN and no markdown."
        )

        # Examples to anchor style (few-shot, but tiny)
        examples = (
            "towel → towel in white; white cotton towel; bath towel on white\n"
            "apple → red apple with green leaf; red apple with green stem; red apple on white\n"
            "soap → soap bar; white soap bar; soap bubbles\n"
            "eggs → eggs in a tray; brown eggs in tray; eggs on white"
        )

        user_prompt = f"""
TARGET_OBJECT: {object_name}

TASK:
Generate a descriptive style caption for image that can be used to create a flash card style or textbook illustration of an obejct

STYLE EXAMPLES:
{examples}

OUTPUT (JSON only; no markdown, no extra text, no trailing commas):
{{
  "caption1": "<text>",
  "caption2": "<text>",
  "caption3": "<text>"
}}
"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.strip()},
            ]
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.2,      # low for stability
                top_p=1,
            )
            raw = resp.choices[0].message.content.strip()
            cleaned = self.clean_json(raw)
            data = json.loads(cleaned)
            # Minimal post-clean: keep only up to max_captions and ensure strings
            out = {}
            i = 1
            for k in sorted(data.keys(), key=lambda x: int(re.sub(r"\D", "", x) or 0)):
                if i > max_captions:
                    break
                val = str(data[k]).strip()
                if val:
                    out[f"caption{i}"] = val
                    i += 1
            if out:
                return out
            # Fallback if empty
            return self._rule_based_fallback(object_name)
        except Exception as e:
            print(f"LLM generation failed, using fallback. Error: {e}")
            return self._rule_based_fallback(object_name)


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    gen = Image_Caption_Filter()
    for obj in ["towel", "apple", "soap", "eggs", "spoon","gas stove"]:
        caps = gen.generate_simple_prompts(obj, max_captions=5)
        print(obj, "->", json.dumps(caps, ensure_ascii=False))
