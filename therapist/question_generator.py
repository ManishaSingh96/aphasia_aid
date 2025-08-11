import os
import openai
from typing import List, Dict, Optional
import random
from therapist.utils import safe_parse_json,clean_json
from therapist.config import url
import httpx
class QuestionGeneratorAgent:
    def __init__(self):
        self._themes_by_severity: Dict[str, List[str]] = {
            "severe": [
                "waking up",
                "bathing",
                "getting ready or dressing up",
                "coomon fruits and vegetables",
                "eating food",
            ],
            "moderate": [
                "kitchen & cooking",
                "bedroom & clothing",
                "living room & electronics",
                "school & stationery",
                "home cleaning supplies",
            ],
            "mild": [
                "market & shopping",
                "travel & transport",
                "clinic & medicines (safe items only)",
                "festivals & home decor",
                "garden & outdoor tools",
            ],
        }

    def generate_questions_for_severity(
        self,
        location=None,
        profession=None,
        language=None,
        severity=None
    ) -> dict:
        """
        Plan a theme from severity (unless theme is provided), then generate a question set.
        Returns a parsed dict (JSON) with keys: object_list, question_list.
        """
        chosen_theme = self._pick_theme(severity)
        raw = self.generate_question(chosen_theme)
        return safe_parse_json(raw)

    def generate_question(self, theme: str) -> str:
        """
        Generate questions for a concrete theme. Returns a JSON string from the model.
        """
        
        system_msg = f"""
        You are a speech-language pathologist conducting a therapy session with a patient who has severe expressive aphasia. 
        The patient struggles with naming even basic objects used in daily life.

         Given a theme, generate a list of 10 common, concrete objects that are visually recognizable and relevant to that theme. 
         These should be everyday items that could be shown as pictures to support naming exercises for language therapy. Avoid abstract concepts.
         Theme:{theme}
         Avoid repetition across sessions and aim for variation in the types of objects.

        Generate a list of 10 distinct, culturally familiar objects that meet the following criteria:

          
          Easy to visualize and physically interact with
          Common in a middle-class Indian household
          
          For each object, create ist common day to day use hindi name and a  "naming from description" type question in Hindi.
          Return the result in valid JSON format like this:
            
          ###Output Format: 

          {{
          
          "object_list": ["object1", "object2", ...],
          "question_list": {{
            "q1": {{
              "object": "object1",
              "object_name_in_hindi":"day to day commom name of object in hindi",
              "question": "Hindi question here",
              "question_type": "naming from description"
            }},
            "q2": {{
              "object": "object2",
              "object_name_in_hindi":"day to day commom name of object in hindi",
              "question": "Hindi question here",
              "question_type": "naming from description"
            }}
            
          }}
        }}
      """
        try:
            messages=[{"role": "user", "content": system_msg}]
            response = httpx.post(
                url,
                json={"input_text": messages},
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["response"]
            content=clean_json(content)
            # print(content)
            return (content)
        except Exception as e:
            print("Error in _generatequestion:", e)
            return None
        # response = openai.ChatCompletion.create(
        #     model="gpt-4o",
        #     messages=[{"role": "system", "content": system_msg},
        #              ]
        # )
        # return response['choices'][0]['message']['content']

    
    def _pick_theme(self, severity: str) -> str:
        sv = (severity or "").strip().lower()
        if sv not in self._themes_by_severity:
            # default to moderate if unknown
            sv = "moderate"
        pool = self._themes_by_severity[sv][:]
        random.shuffle(pool)
        return pool[0]

   


