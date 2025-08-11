from typing import Dict, Tuple
import json 
from therapist.utils import clean_json
from therapist.config import url
import httpx

class ValidatorAgent:
    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def validate(self, object_name,generated_hint: str, initial_question: str, user_response: str) -> Tuple[bool, str]:
        
        system_prompt="""You are a strict validator evaluating descriptive hints for aphasia therapy.

    ## You will receive:
    1. Target Word: the exact object name we are trying to help the patient recall (do not reveal it)
    2. Generated Hint: the latest descriptive hint provided
    3. Hint History (map[int → string]): all previous descriptive hints given in this session
    4. Initial Question: the naming prompt given to the patient
    5. Patient Response History (map[int → string]): how the patient has responded so far

    ---

    ## Your Task:
    Decide whether the **Generated Hint** follows **all rules** for an ideal descriptive hint.

    ### Evaluation Criteria:
    [ ] **Language simplicity**: Uses short, plain Hindi understandable by a 5-year-old or elderly person.
    [ ] **Tone**: Warm, friendly, supportive — like a caring family member or therapist.
    [ ] **Contextual clue**: Gives a clue about use, location, appearance, or sensory features — without naming the object.
    [ ] **Progression**: Moves one step closer than previous hints toward identifying the object; gradual reveal.
    [ ] **Anchored to target**: Clues must relate only to the target word — no drift to unrelated items.
    [ ] **No repetition**: Does not reuse wording or descriptions from Hint History.
    [ ] **Natural conversation**: If the latest patient response is partially correct or related (e.g., says "sabun" when target is "shampoo"), acknowledges it and naturally bridges to the target (e.g., “हाँ, साबुन से भी सफाई होती है, लेकिन ये सिर पर इस्तेमाल होता है…”).
    [ ] **Length**: Hint is short — ideally one line.
    [ ] **No direct answer**: Does not reveal the target word.
    [ ] **No abstract/poetic language**: Avoids figurative or overly complex expressions.
    [ ] **Avoid repeating the original question**: Wording should be new.

    ---

    ## Self-Validation Steps (internal thinking — do not output):
    1. Compare Generated Hint with Target Word and Hint History for relevance and progression.
    2. Check if it adapts to the **latest** patient response.
    3. Ensure it’s short, simple, and conversational.
    4. Confirm it moves closer to the target without revealing it.

    ---
    
Return only a valid JSON dictionary like this — **no extra quotes or characters**:
{{"accepted": true if correct false if not correct , "reason": "Brief explanation here."}}

    """
         # Construct validation request
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
            Object name:{object_name}
            Generated Hint: {generated_hint}
            Initial Question: {initial_question}
            Patient Response: {user_response}
            """}
        ]

        try:
            messages=self.messages
            response = httpx.post(
                url,
                json={"input_text": messages},
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["response"]
            content=clean_json(content)
            decision_dict = json.loads(content)
            return (decision_dict["accepted"], decision_dict["reason"])

            
        except Exception as e:
            print(f"Validation error: {str(e)}")
            return (False, "API call failed during validation")
