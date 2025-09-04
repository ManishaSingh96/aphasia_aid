
import httpx
from utils import safe_parse_json,clean_json
# from therapist.config import url
import os
import openai
import json
class CaptionGenerator:
    def __init__(self):
        openai.api_key=os.getenv("OPENAI_API_KEY") 
    def generate_positive_and_negative_captions(self, object_name):

        user_prompt = """
        You are a regex pattern generator that BLACKLISTS captions unsuitable for flashcard-style image generation from a large (CLIP) dataset.

        Task:
        Given a **target object**, think carefully and broadly about what makes a caption NON-suitable for a clean, single-object flashcard image of that object. Then produce a list of Python-compatible, plural-aware regex patterns that MATCH such non-suitable captions so they can be excluded.

        Think for yourself (do not list your reasoning). Consider how real captions in a web-scale dataset are written and what signals that the image is NOT a plain, isolated, real-life depiction of the target object.

        Key constraints to internalize BEFORE writing patterns:
        - Flashcard suitability means a single, real-life object on a plain/neutral background, minimal wording, no extra objects or scene context.
        - Non-suitable captions include (but are not limited to): multiple or unrelated objects; scene/place/furniture context; people/animals; brand/logos/metadata; numbers/IDs/URLs/hashtags; artistic/illustrated renders; and non-real forms/derivatives (e.g., “apple pie”, “iPhone Apple logo”, “egg bhurji”, “blue/golden eggs”, “vector towel”).
        - For each pattern, ensure the object is referenced in SINGULAR or PLURAL (use `objects?` form for plural awareness).

        Regex requirements:
        - Use `\\b` for word boundaries and `.*` for flexible gaps.
        - Use plural-aware forms of the target object, i.e., `\\b{{OBJ}}s?\\b` where `{{OBJ}}` is the singular lemma.
        - Prefer concise patterns that generalize; include both object-first and context-first variants where helpful.
        - Escape backslashes for JSON and Python compatibility (double backslashes).
        - Do NOT output explanations—only JSON with the patterns.

Output format (JSON only):
{
  "NEGATIVE_PATTERNS": [
    "pattern_1",
    "pattern_2",
    ...
  ]
}

Now, infer and return a diverse set of negative regex patterns that match captions you consider NON-suitable for a flashcard-style image of this object. Output only the JSON.


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
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=.1
        )
        # response = httpx.post(
        #         url,
        #         json={"input_text": messages},
        #         timeout=60
        #     )
        # response.raise_for_status()
        response=response.choices[0].message.content.strip()
        content=clean_json(response)
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
    
if __name__ == "__main__":
    img=CaptionGenerator()
    top_caption=img.generate_positive_and_negative_captions(object_name='towel')
    
