import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv

# Load your OpenAI key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Categories suitable for image generation
image_friendly_categories = [
    "Image-Based Naming",
    "Action Naming",
    "Syllable-Based Speaking",
    "Descriptive Speaking",
    "Functional Sentence Construction",
    "Yes/No Questions",
    "Object Identification",
    "Function Matching"
]

# Load questions from JSON
with open("therapy_questions_with_images.json", "r", encoding="utf-8") as f:
    all_questions = json.load(f)

# Collect all image-friendly questions with their image prompts
image_questions = []
for category in image_friendly_categories:
    if category in all_questions:
        # all_questions[category] is a list of dicts with "question" and "image_prompt"
        for item in all_questions[category]:
            question = item.get("question", "").strip()
            image_prompt = item.get("image_prompt", "").strip()
            if question and image_prompt:
                image_questions.append({
                    "category": category,
                    "question": question,
                    "image_prompt": image_prompt
                })

# Randomly pick 5 questions for image generation
selected_questions = random.sample(image_questions, 5)

# Create directory to save metadata files
os.makedirs("image_questions", exist_ok=True)

# Store results for saving to new JSON
output_data = []

# Generate and save images
for i, item in enumerate(selected_questions, 1):
    category = item["category"]
    question = item["question"]
    prompt = item["image_prompt"]

    print(f"[{i}] Generating image for question: {question}")
    print(f"    Using image prompt: {prompt}")

    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="512x512",
            n=1
        )
        image_url = response.data[0].url

        # Save metadata to text file (optional)
        with open(f"image_questions/question_{i}.txt", "w", encoding="utf-8") as f:
            f.write(f"Category: {category}\nQuestion: {question}\nImage prompt: {prompt}\nImage URL: {image_url}\n")

        # Append to output data
        output_data.append({
            "category": category,
            "question": question,
            "image_prompt": prompt,
            "image_url": image_url
        })

        print(f"✅ Image generated and URL saved: {image_url}")

    except Exception as e:
        print(f"❌ Failed to generate image for question: {question}")
        print(e)

# Save all generated question-image_url pairs in a new JSON file
with open("therapy_questions_with_generated_images.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)

print("✅ Saved generated images info to therapy_questions_with_generated_images.json")
