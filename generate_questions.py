import openai
import os
import json
import re
from time import sleep
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

categories = {
    "Descriptive Clue": "e.g., “This is red, round, and grows on a tree. You eat it.” → Apple",
    "Use-Based Naming": "e.g., “What do you use to brush your teeth?” → Toothbrush",
    "Image-Based Naming": "e.g., [Show image of cow] “What is this?”",
    "Category Recall - 3 items": "e.g., “Name 3 fruits.”",
    "Category Recall - 5 items": "e.g., “Name 5 animals that live in water.”",
    "Action Naming": "e.g., [Image of someone running] “What is the person doing?” → Running",
    "Syllable-Based Speaking": "e.g., [Image of dog] “Say: dog”",
    "Descriptive Speaking": "e.g., [Image of bus] “Say what it is and what it does.”",
    "Functional Sentence Construction": "e.g., [Image of toothbrush] “Say a sentence using this.”",
    "Yes/No Questions": "e.g., “Is this a fruit?” [image of apple]",
    "Object Identification": "e.g., “Point to the one you eat: soap, apple, pencil”",
    "Function Matching": "e.g., “What do you use to cut? Knife or spoon?”",
    "Follow Command (1-step)": "e.g., “Touch your head.”",
    "Follow Command (2-step)": "e.g., “Pick up the spoon and give it to me.”",
    "WH- Questions": "e.g., “Where do you sleep?” → Bed",
    "Functionality Questions": "e.g., “How do you use a knife and fork together?”",
    "Short Passage Q&A": "e.g., After reading: “In the morning, I wake up, brush my teeth, and eat breakfast.” → “What do you use to brush?”"
}

# Updated prompt focusing on daily life activities
system_prompt = """
You are an expert language therapist who creates speech therapy questions for people with aphasia. 
Use very simple and culturally familiar language. Focus especially on everyday daily activities like:
bathing, eating, dressing, combing hair, ironing clothes, buttoning shirts, brushing teeth, cooking, taking a bus, or using simple tools.
Avoid abstract topics. Keep questions short, friendly, and easy to understand.
"""

def generate_questions_with_prompts(category, example_format):
    user_prompt = f"""
Generate 30 therapy questions for the category: **{category}**.
Include questions about daily Indian activities like brushing teeth, ironing shirts, cooking food, buttoning clothes, taking a bath, or boarding a bus.
Make questions culturally relevant to Indian profiles.
Use this example format: {example_format}
Return only a numbered list of 30 questions. For each question, also generate a one-line DALL·E style image description prompt that visually represents the scenario or item involved.
Output JSON format:
[
  {{
    "question": "...",
    "image_prompt": "..."
  }},
  ...
]
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    content = response.choices[0].message.content.strip()

    # Extract JSON inside triple backticks if possible
    json_match = re.search(r"```json\s*(\[\s*{.*?}\s*])\s*```", content, re.DOTALL)

    if json_match:
        json_str = json_match.group(1)
    else:
        # Fallback: Try to extract first valid-looking JSON list anywhere in the content
        fallback_match = re.search(r"(\[\s*{.*?}\s*])", content, re.DOTALL)
        if fallback_match:
            json_str = fallback_match.group(1)
        else:
            print(f"⚠️ Failed to extract JSON block for category: {category}")
            print(f"🔍 Raw content:\n{content[:500]}...")
            return []

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error for category '{category}': {e}")
        print(f"🔍 Raw content returned:\n{content[:500]}...")  # Show snippet for debugging
        return []

if __name__ == "__main__":
    all_data = {}

    for category, example in categories.items():
        print(f"🔄 Generating for: {category}")
        try:
            questions = generate_questions_with_prompts(category, example)
            all_data[category] = questions
            sleep(2)  # polite pause
        except Exception as e:
            print(f"❌ Failed for {category}: {e}")

    # Save all generated data to JSON file
    with open("therapy_questions_with_images.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("✅ Saved all questions and image prompts to therapy_questions_with_images.json")
