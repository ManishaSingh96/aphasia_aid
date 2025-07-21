import os
import json
# from prompt import prompt,evaluator_agent_prompt
from pydub import AudioSegment
from pydub.playback import play
import io,re
from therapist.th_prompt import system_prompt, evaluator_agent_prompt
import httpx
from utils import clean_json
class generate_therapist:
    def __init__(self):        
        self.prompt=system_prompt
        self.evaluator=evaluator_agent_prompt
        self.url="http://localhost:7878/api/llm/generate"
    def _generatequestion(self, location, profession, language):
        prompt_filled = self.prompt.format(
            location=location,
            profession=profession,
            language=language,
            )
        
        ##### add validaton agent which will check if the language is correct if not rerun
        try:
            messages=[{"role": "user", "content": prompt_filled}]
            response = httpx.post(
                self.url,
                json={"input_text": messages},
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["response"]
            content = clean_json(content)
            return json.loads(content)
        except Exception as e:
            print("Error in _generatequestion:", e)
            return None
    def _validate(self,step_type,question,object,user_ans,correct_ans):
        user_prompt = f"""
        "step_type":{step_type}
        Question: {question}
        Object Name:{object}
        User Answer: {user_ans}
        Expected Answers: {correct_ans}
        """
        messages=[{"role": "system", "content": self.evaluator},
                      {"role": "user", "content": user_prompt}]
        try:
            response = httpx.post(
                self.url,
                json={"input_text": messages},
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["response"]
            content = clean_json(content)
            return json.loads(content)
        except Exception as e:
            print("Error in validating:", e)
            return None
        
    def main(self,location, profession, language):
        questions=self._generatequestion(location, profession, language)
        return questions
    
    def evaluate(self,step_type,question,object,user_ans,correct_ans):
        response=self._validate(step_type,question,object,user_ans,correct_ans)
        return response