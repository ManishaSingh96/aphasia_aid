
import os , httpx
from therapist.config import url
class QuestionFramingAgent:
    def __init__(self):
        pass
    def frame_question_and_hint(self, object_name,question_type):
        prompt = f"""
        Frame a simple {question_type} style question in Hindi to help a patient with aphasia name this object: "{object_name}"
        Format:
         <description-style question>
        """
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        messages=[{"role": "user", "content": prompt}]
        response = httpx.post(
            url,
            json={"input_text": messages},
            timeout=60
        )
        response.raise_for_status()
        content = response.json()["response"]
        print(content, ' inside framer')
        return content
    
