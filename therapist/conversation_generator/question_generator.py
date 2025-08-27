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
                "waking up in the morning",
                "bathing and grooming",
                "getting ready or dressing up",
                "common fruits and vegetables",
                "eating and drinking and cutlery you use",
                "common staples and food and cutlery you use in eating"
                "common household items or furniture"
            ],
            "moderate": [
                "basic electronic items",
                "things you see in your house or household items",
                "dressing",
                "fruits and vegetables"
                "common therapy room objects",
                "common fruits and vegetables",
                "comon household chores items",
                "things you use in eating and drinking",
                "modes of transport"
            ],
            "mild": [
                "grocery shopping",
                "travelling",
                "dealing with money",
                "festivals & home decor",
                "modes of transport",
                "monumets or famous places or famous cities",
                "things you use in your profession",


            ],
        }

    def generate_questions_for_severity(
        self,
        age=None,
        gender=None,
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
        print('checkpoint: 1 : ', chosen_theme)
        raw = self.generate_question(age,gender,location,profession,severity,chosen_theme)
        return safe_parse_json(raw)

    def generate_question(self, age: str,gender: str,location: str,profession: str,severity: str,theme: str) -> str:
        """
        Generate questions for a concrete theme. Returns a JSON string from the model.
        """
        
        system_msg = f"""
        
You are a **question generator** for a speech therapy program, creating object-based naming questions for aphasia patients.  
Your goal is to generate 10  object names in english that help patients recognize and name items, supporting their ability to understand and speak.


### Key Requirements:
1. **Theme-based selection**: You will be given a theme (e.g., "Eating & Drinking", "Bathing & Grooming").
2. **Patient persona**: Includes severity (severe, moderate, mild), location (urban/rural), age group, gender, profession, and lifestyle.
3. **Relevance to persona**:
   - Severe: Focus on **Activities of Daily Living (ADL)** objects (e.g., water, soap, plate) that are essential for basic chores.
   - Moderate: Include **Instrumental Activities of Daily Living (IADL)** objects (e.g., shopping, cooking, transport items).
   - Mild: May include profession-related, city-specific, and more complex objects.
   - Adapt to location: For rural, include culturally familiar objects (e.g., chulha, charpai); for urban, use relevant items (e.g., gas stove, refrigerator).
4. **Simplicity**:  
   - Avoid complex, uncommon, or brand-specific objects.
   - Prefer words the patient is likely to know and use daily.
   - For example, when talking about eating, use "plate" or "cup" instead of "tissue".
   -Do not use words with more than three syllables
5. **Language**:
   - All questions in **simple, everyday Hindi**.
   - Object names in Hindi should be the **common day-to-day spoken version**.


### Guidelines
1.Match the object names to severity of patient .
Understand that severe patients can only understand very basic day to day things.Mild or
 moderate severity patient might understand things related to profession.And even in that mild patients can understand maybe more complex words but moderate might not
2.Match the obejct list to patient persona as well ex city, lifestyle,gender,age group
3.Modify the theme accordingly if does not suit the persona
4.Include common objects as well - walking stick,pen,paper,book,clock etc


### Keep in mind
1.Object names are simple and in english
2.There are 10 objects in the list 


### Output Format (JSON):

{{
  "object_list": ["object1", "object2", ...],}}

### Example:
If theme = "Eating & Drinking" and persona = Severe, Rural:
- Object list may include: ["plate", "cup", "spoon", "chulha", "water"]

"""

 
        try:
            messages=[
                {"role": "user", "content": system_msg},
                {"role": "user", "content": f"""
                Theme:{theme}
                Severity: {severity}
                Location: {location}
                Profession: {profession}
                Age:{age}
                Gender:{gender}

                """}
                ]
            response = httpx.post(
                url,
                json={"input_text": messages},
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["response"]
            content=clean_json(content)
            print(content)
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

   


