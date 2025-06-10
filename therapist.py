from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from prompt import prompt,evaluator_agent_prompt
from pydub import AudioSegment
from pydub.playback import play
import io,re

load_dotenv()

class generate_therapist:
    def __init__(self, model="gpt-4o", assistant_name="Speech Therapist Assistant"):
        self.client = OpenAI() 
        self.model = model
        self.prompt = prompt
        self.evaluator_agent_prompt=evaluator_agent_prompt
        self.assistant_name = assistant_name

    def call_question_generation_agent(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": self.prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        content=self.clean_json(content)
        exercise_sets = json.loads(content)
        return exercise_sets
    
    def clean_json(self,text):
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
            print("match found")
        else:
            json_text=text
            print("No match found.")
        return json_text

    def call_tts(self, text):
        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )
        audio_data = io.BytesIO(response.content)
        audio_segment = AudioSegment.from_file(audio_data, format="mp3")
        play(audio_segment)

    def call_evaluator_agent(self,object_name, user_msg, step):
        user_prompt = f"""
        "step_type":{step.get('step_type')}
        Question: {step.get('question')}
        Object Name:{object_name}
        User Answer: {user_msg}
        Expected Answers: {step.get('expected_answers','NA')}
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.evaluator_agent_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0.7
        )


        return response.choices[0].message.content
    
    def call_image_generator_agent(self,object):
        user_prompt=f"""A cartoon style clear illustration of a {object}"""

        response = self.client.images.generate(
        model="dall-e-2",
        prompt=user_prompt,
        size="512x512",
        n=1
        )

        image_url = response.data[0].url

        return image_url







