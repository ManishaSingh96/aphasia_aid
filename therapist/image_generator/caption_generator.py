
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
        1. Generate 10 **positive captions** that describe the TARGET_OBJECT in a descriptive, textbook/flashcard style.
        - Captions should be short.
        - Only the object itself should be described (no people, no extra objects).
        - Assume a plain or neutral background.
        - Use the most common and simple variants of the object.

        2. Generate 10 **negative captions** that are unsuitable for textbook/flashcard style.
        - These may include people, other objects, or uncommon/novel variants.
        - Examples: object being used by people, in busy scenes, branded versions, or as part of a recipe.

        OUTPUT FORMAT:
        Return **strict JSON only**, with the following structure and no extra text, no markdown, no trailing commas:

        {{
        "positive_captions": [
            "caption text 1",
            "caption text 2",
            ...
            "caption text 10"
        ],
        "negative_captions": [
            "caption text 1",
            "caption text 2",
            ...
            "caption text 10"
        ]
        }}

        FEW-SHOT EXAMPLES:

        TARGET_OBJECT: Apple
        {{
        "positive_captions": [
            "A red apple with green leaves",
            "A red apple with green stem",
            "A whole green apple",
            "A single apple on plain background",
            "A shiny red apple",
            "A plain yellow apple",
            "A ripe apple on white background",
            "A fresh apple with smooth skin",
            "A single apple centered in frame",
            "A clean red apple with stem"
        ],
        "negative_captions": [
            "Apple pie on a plate",
            "Apple wine in a glass",
            "Girl plucking apple from tree",
            "A hand holding an Apple phone",
            "A basket filled with apples",
            "An apple orchard with many trees",
            "Cut apple slices on a plate",
            "Caramel apple on a stick",
            "Apple with chocolate topping",
            "Apple logo on a laptop"
        ]
        }}

        TARGET_OBJECT: Towel
        {{
        "positive_captions": [
            "A plain white towel",
            "A folded towel",
            "A towel hanging on a hook",
            "A rolled towel",
            "A clean bath towel",
            "A hand towel on plain background",
            "A grey towel folded neatly",
            "A stack of white towels",
            "A striped towel on plain background",
            "A single towel centered in frame"
        ],
        "negative_captions": [
            "A girl wearing a towel on the beach",
            "A man drying with a towel",
            "A towel with cartoon characters",
            "Towel on hotel bed with flowers",
            "A dog wrapped in a towel",
            "A towel rack in a bathroom",
            "A towel with brand logo",
            "Two people sharing a towel",
            "A branded towel displayed in a store",
            "A towel used in a beach party"
        ]
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
    
