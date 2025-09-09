
import httpx
from therapist.utils import safe_parse_json,clean_json
from therapist.config import url
import json
class CaptionGenerator:
    def __init__(self):
        pass
    def generate_positive_and_negative_captions(self, object_name):
        system_prompt = """
        You are a caption generator that generates suitable captions for flashcard style images 
        used in naming from description exercise for speech therapy.

        """
                

        user_prompt = f"""
        INPUT:
        TARGET_OBJECT: {object_name}

        TASK:
        1. Generate 5 **positive captions** that describe the TARGET_OBJECT in a descriptive, textbook/flashcard style.
        - Each caption should describe the object in a common and focused way, suitable for a flashcard image.
        - Use the most common and simple forms of the object, especially as seen in Indian households.
        - Captions must be short (3–10 words), natural, and generic.
        - The object should appear alone or with minimal natural context with the most common and basic adjuncts 
        - You may include **inherent parts or effects** (e.g., with bubbles, with stem).
        - You may optionally end captions with **“on white background”** to emphasize clean flashcard style.

        2. Generate 5 **negative captions** that are unsuitable for textbook/flashcard style.
        - These may include people, animals, additional unrelated objects, busy scenes, uncommon/novel variants, or branded versions.
        - Scene/usage/location/contextual words are encouraged in negatives (e.g., “on table”, “in kitchen”, “during bath”, “held by child”).
        - Examples: object being used, in a cluttered or real-world scene, cartoon/stylized versions, text written on object, etc.

        OUTPUT FORMAT:
        Return **strict JSON only**, with the following structure and no extra text, no markdown, no trailing commas:

        {{
        "positive_captions": [
            "caption text 1",
            "caption text 2",
            ...
            "caption text 5"
        ],
        "negative_captions": [
            "caption text 1",
            "caption text 2",
            ...
            "caption text 5"
        ]
        }}

        ALLOWED IN POSITIVE CAPTIONS:
      - **Most common flashcard-style form of the object**  
        Example:
        - soap → round/plain soap bar  
        - apple → red apple with stem  
        - eggs → white eggs in tray, eggs in nest

      -You may include inherent effects only if they directly modify the object (e.g., “soap bar with bubbles” is allowed; “soap bubbles on a surface” is not)
      - Variations: include different **valid flashcard variations** by mixing at most ONE adjunct per caption:
        • Inherent parts/effects: with stem, with leaves, with shell, with bubbles
        • simple containers/supports: in tray, in bowl, in basket, in carton, in nest, in soap dish, on plate, on table
        - Colors:
        • In general, DO NOT use color adjectives.
        • **Exception (canonical color rule):** If a specific color is the most common flashcard depiction for the object,
            you may use ONLY that canonical color exactly once among the positives.
            Examples of canonical colors:
            - apple → “red apple” or “red apple with green stem”
            - eggs → “white eggs”
            - milk → “white milk in glass”
            Do not invent other colors.
        - Forbidden in positives: people/animals, brands/logos/text, usage actions (holding, eating, cutting, cracking, cooking, pouring),
        busy scenes/locations (kitchen, garden, cafe, street), cartoon/clipart/drawing words.
      - Optional: “on white background” at the end of a caption

        FORBIDDEN IN POSITIVE CAPTIONS:
        -Captions where the main subject is not the target object (e.g., "soap bubbles", "egg yolk", "towel rack", "apple tree", etc.)
       - Do not accept captions where the object is only implied or missing. The target object must be explicitly present as the main noun.
        - People or animals (e.g., man, child, cat, dog)
        - Uncommon variants or fantasy forms
        - Brand names or logos
        - Text/words visible on the object
        - Real-world scene indicators (e.g., kitchen, street, café, garden, hotel, beach)
        - Usage actions (e.g., holding, eating, using, applying, cooking, painting)

        FEW-SHOT EXAMPLES:

        TARGET_OBJECT: Soap
        {{
        "positive_captions": [
            "soap bar with bubbles on white background",
            "soap bar in soap dish ",
            "rectangular soap bar ",
            "stacked soap bars ",
            "simple soap bar centered"
        ],
        "negative_captions": [
            "woman washing hands with soap",
            "baby holding a cartoon soap",
            "soap bottle in kitchen sink",
            "soap on hotel bathroom counter",
            "a pile of multicolored soaps",
        }}

        TARGET_OBJECT: Eggs
        {{
        "positive_captions": [
            "eggs in a tray ",
            "eggs in a nest ",
            "eggs in a bowl on table",
            "set of eggs in carton",
            "three whole eggs",
  
        ],
        "negative_captions": [
            "chef cracking eggs into a pan",
            "child painting colorful easter eggs",
            "fried eggs with toast on plate",
            "egg yolk spilling in kitchen",
            "duck sitting on eggs in mud",
        }}



        """
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=messages
        # )
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
    
