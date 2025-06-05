import openai
from dotenv import load_dotenv
import os
# Load your OpenAI key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key  # Or use os.getenv("OPENAI_API_KEY")

import openai

# Make sure you've set OPENAI_API_KEY as env variable or assign it directly
client = openai.OpenAI()

hindi_text = "नमस्ते! आप कैसे हैं? कृपया इसे धीरे बोलें।"

response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",  # alloy, echo, fable, onyx, nova, or shimmer
    input=hindi_text
)

# Save to file
with open("hindi_speech.mp3", "wb") as f:
    f.write(response.content)

print("✅ Hindi speech saved to 'hindi_speech.mp3'")

