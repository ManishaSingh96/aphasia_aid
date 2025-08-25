from therapist.utils import safe_parse_json,clean_json
from therapist.config import url
import httpx

class EvaluatorAgent:
    def __init__(self):
        pass
    def evaluate_and_predict(self, object,question,question_type,patient_response):
        evaluation_prompt = f"""
    You are an evaluator in a speech therapy system for aphasia patients. Assume the patient's response is already non-gibberish.

Inputs:
- Question (Hindi): {question}
- Question Type: {question_type}    // e.g., function-use, picture naming, category, description
- Patient Response (transcribed): {patient_response}
- Target Object (therapist’s intended object): {object}

Your job:
1) Judge whether the response semantically answers the question with respect to the Target Object.
   Return exactly one of: "Correct", "Partially Correct", "Incorrect".
2) Return a short Reason (1–2 sentences) in **English** that explains the decision.
   - Do not reveal the target word.
   - Keep the Reason factual (e.g., “mentions ingredient not the object”, “same category but not the intended item”, “fits function and category”).

Decision rules (NO exact string match required):
- Correct:
  - Synonym/regional/phonetic variant of the target object, OR
  - Clearly satisfies the question’s intent for the target (right function, category, specificity, context).
- Partially Correct:
  - Reasonable alternative in the same broader category but not the intended item, OR
  - Only the category/function is given without the specific item, OR
  - Closely related tool/object used in the same activity but not the one asked.
- Incorrect:
  - Unrelated category or wrong function, OR
  - Names a material/ingredient/context instead of the object (e.g., water vs shampoo), OR
  - Brand-only that doesn’t clearly identify the object type.

Output (strict JSON only; no extra text):
{{
  "Evaluation": "<Correct | Partially Correct | Incorrect>",
  "Reason": "<short English explanation>"
}}

Examples:

Input:
Question: "जैसे आप बाल धोते हो, क्या लगाते हो?"
Question Type: "function-use"
Patient Response: "पानी"
Target Object: "शैम्पू"
Output:
{{"Evaluation":"Incorrect","Reason":"Mentions an accompanying material (water) rather than the applied product the question asks for."}}

Input:
Question: "बाहर जाते समय पैरों में क्या पहनते हैं?"
Question Type: "function-use"
Patient Response: "चप्पल"
Target Object: "जूते"
Output:
{{"Evaluation":"Partially Correct","Reason":"Same category (footwear) but not the intended item; provides a related alternative."}}

Input:
Question: "दाँत साफ़ करने के लिए क्या इस्तेमाल करते हो?"
Question Type: "function-use"
Patient Response: "ब्रश"
Target Object: "टूथब्रश"
Output:
{{"Evaluation":"Correct","Reason":"Fits the function and is an acceptable synonym/variant of the intended object."}}

  
"""

        # user_input = f"Question: {question.strip()}\nPatient Response: {patient_response.strip()}"

        messages=[{"role": "user", "content": evaluation_prompt}]
        try:
            response = httpx.post(
                    url,
                    json={"input_text": messages},
                    timeout=60
                )
            response.raise_for_status()
            content = response.json()["response"]
            content=clean_json(content)
            return (content)
        except Exception as e:
            print("Error in _evaluatequestion:", e)
            return None
        

