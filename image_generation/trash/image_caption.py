import os
import openai
from config import url
import httpx
class Image_Generation_Caption:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
    def generate_image(self, object_name):
        prompt = f"""
You are writing a single-sentence caption for an image to be used as a flashcard for aphasia therapy.

TARGET OBJECT: {object_name}

REQUIREMENTS (the sentence must imply all of these):
- Exactly one {object_name}, centered.
- Plain white or light solid background.
- High-resolution, well-lit, in-focus, photographic (not a cartoon).
- No other objects or text; educational, textbook-like style.
- Use bright, vibrant colors wording.

OUTPUT RULES:
- Return EXACTLY ONE sentence, 12–24 words.
- Start with: "A high-resolution photo of a single {object_name}".
- Include the words: centered, plain background, well-lit, in focus, no other objects, textbook-like.
- Do NOT return only the word "{object_name}". Do NOT include quotes or bullet points.

Example outputs:
- A high-resolution photo of a single apple, centered on a plain background, well-lit and in focus, bright colors, textbook-like, no other objects.
- A high-resolution photo of a single toothbrush, centered with a plain background, well-lit and in focus, vibrant, textbook-like, no other objects.

"
        Format:
         <image caption>
        """
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        messages=[{"role": "user", "content": prompt},
                  {"role": "user", "content": object_name}]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages
        )
        response=response.choices[0].message.content.strip()
        
        return response
    

if __name__ == "__main__":
    generator = Image_Generation_Caption()
    object_name = "apple" 
    caption = generator.generate_image(object_name)
    print(f"Generated caption for '{object_name}': {caption}")
    
