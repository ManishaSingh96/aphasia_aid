
import httpx
from therapist.utils import safe_parse_json,clean_json
from therapist.config import url
import os
import openai
import json
class PatternGenerator:
    def __init__(self):
        pass
    def generate_negative_patterns(self, object_name):

        user_prompt = """
        You are a regex pattern generator that BLACKLISTS captions unsuitable for flashcard-style image generation from a large (CLIP) dataset.

Task:
Given a **target object**, think carefully and broadly about what makes a caption NON-suitable for a clean, single-object flashcard image of that object. Then produce a list of Python-compatible, plural-aware regex patterns that MATCH such non-suitable captions so they can be excluded.

Think for yourself (do not list your reasoning). Consider how real captions in a web-scale dataset are written and what signals that the image is NOT a plain, isolated, real-life depiction of the target object.

Calibrated scope (NOT TOO TIGHT):
- Prefer **general families** of negatives (people/animals, actions/usage, busy scenes/locations, brands/logos/text, recipes/derived forms, non-real/art styles) over ultra-specific phrases.
- **Avoid over-blocking legitimate flashcard positives.** Do NOT target: 
  - backgrounds like “on white background” / “plain background”
  - simple containers/supports: tray, bowl, basket, carton, nest, soap dish, plate, table
  - inherent parts/effects: stem, leaves, bubbles, shell, frame, handle
- When needed, you may use proximity limits (e.g., within 0–4 words of {{OBJ}}s?) instead of “match anywhere” to reduce false positives.
- Do not create catch-alls like “any preposition + {{OBJ}}s?” or patterns that ban the allowed containers/backgrounds above.

Regex requirements:
- Use `\\b` for word boundaries and `.*` for flexible gaps.
- Use plural-aware forms of the target object, i.e., `\\b{{OBJ}}s?\\b` where `{{OBJ}}` is the singular lemma.
- Prefer concise patterns that generalize; include both object-first and context-first variants where helpful.
- Add **one regex** that filters captions with the word **illustration** or **illustrations**.
- Escape backslashes for JSON and Python compatibility (double backslashes).
- Output only JSON with the patterns (no explanations).

Negative categories to cover (broad but safe):
- People/animals interacting with the object (holding, using, eating, wearing, etc.)
- Actions/usage that imply non-flashcard scenes (cooking, baking, cracking, pouring, applying, serving)
- Busy scenes/locations (kitchen, garden, street, market, hotel, party, picnic, bathroom), but avoid banning “on white background” or “plain background”
- Brands/logos/text/metadata (brand, logo, label, sticker, trademark, barcode, QR, hashtag, URL)
- Non-real/art styles (cartoon, clipart, vector, drawing, sketch, render, CGI, 3D model, digital art)
- Derived/recipe/product forms (e.g., for {{OBJ}} = apple: apple pie/juice/cider; for eggs: omelette/scramble; for soap: liquid soap, dispenser, packaging focus)
- Packaging/commerce emphasis (box, wrapper, price tag, store shelf) — but do not block minimal allowed containers/supports

Output format (JSON only):
{
  "NEGATIVE_PATTERNS": [
    "pattern_1",
    "pattern_2",
    ...
  ]
}


        """
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        messages = [
                {"role": "user", "content": user_prompt},
                {"role": "user", "content": f"""
                 Target Object: {object_name}"""}
            ]
        response = httpx.post(
                url,
                json={"input_text": messages},
                timeout=60
            )
        response.raise_for_status()
        data=response.json()["response"]
        content=clean_json(data)
        print(content)
        content=json.loads(content)

        # response = httpx.post(
        #     url,
        #     json={"input_text": messages},
        #     timeout=60
        # )
        # response.raise_for_status()
        # content = response.json()["response"]
        # print(content, ' inside framer')
        return content

    
