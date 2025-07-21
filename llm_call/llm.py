import openai
import os

class OpenAITextGenerator:
    def __init__(self, model_name="gpt-4o"):
        self.api_key = os.getenv("OPENAI_API_KEY")  # Load from env variable
        self.model_name = model_name

        if not self.api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable.")

        openai.api_key = self.api_key

    def generate(self, input_text):
        if hasattr(input_text[0],"dict"):
            input_text=[m.dict() for m in input_text]
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=input_text,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
