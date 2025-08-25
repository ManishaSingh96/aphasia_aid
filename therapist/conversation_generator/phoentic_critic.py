import openai
import os
from typing import Tuple
import json
from therapist.utils import safe_parse_json,clean_json
from therapist.config import url
import httpx

class PhoneticValidatorAgent:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.messages = []

    def validate(self, object_name:str,generated_hint: str, initial_question: str, user_response: str) -> Tuple[bool, str]:
      system_prompt="""
      You are an **evaluation agent** validating **phonetic hints** generated for **aphasia patients** learning to speak common words.

      Your job is to determine whether the **hint is accurate, helpful, and appropriate**, based on the **patient’s spoken attempt** and the **target word**.


      ###  You Will Be Given:
      * **Object name **: The object name /target word we are trying to pronounce
      * **Question**: The naming prompt asked to the patient (includes the target word)
      * **Patient Response**: What the patient said
      * **Generated Hint**: The phonetic hint provided by the phonetic agent

      ### Evaluation Criteria:

      Evaluate whether the hint is acceptable using the following checklist:

      #### 1. **Target Alignment**

      * Does the hint **point toward the correct target word** for ex if alaram you should prompt to say alarm not ghadi ?
      * It must use **phonemes and syllables** that belong to the target word.
      * ❌ **Reject** if it guides to a **different word** (e.g., hint is about “घड़ी” when the correct word is “अलार्म”).

      #### 🔹 2. **Phonetic Accuracy**

      * Does the hint use the **correct initial sounds** (e.g., “घ” vs “ग”)?
      * ❌ **Reject** if the **wrong consonant, vowel, or aspiration** is used — even if close.
      * For example:

        * “घड़ी” should start with **“घ”**, not “ग”
        * “थाली” should start with **“थ”**, not “ट”

      #### 🔹 3. **Adaptiveness**

      * Does the hint respond correctly to the **patient’s actual response**?
      * If the response is **gibberish**, the hint should:

        * Start with **basic phonetic cues**
        * Offer **gentle correction**
        * Motivate with phrases like: “कोई बात नहीं, चलो आवाज़ पहचानते हैं…”

      #### 🔹 4. **Progressive Phonetic Guidance**

      * Does the hint build the word **step by step** through syllables?
      * The hint should not jump ahead or overload the patient.
      * It should scaffold the word in a **natural sequence**.

      #### 🔹 5. **Motivational and Clear Tone**

      * Is the language **short, friendly, and encouraging**?
      * Does it **motivate the patient** to continue speaking?

      #### 🔹 6. **Avoidances**

      * ❌ Do **not** say the full target word
      * ❌ Do **not** describe the object
      * ❌ Do **not** use long, abstract explanations


      **Output Format:**
Return only a valid JSON dictionary like this — **no extra quotes or characters**:
{{"accepted": true if correct false if not correct , "reason": "Brief explanation here."}}        
              """

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
          print("content",content)
          decision_dict = json.loads(content)
          print("go")
          print("reason",decision_dict)
          return (decision_dict["accepted"], decision_dict["reason"])

      except Exception as e:
          print(f"Validation error: {str(e)}")
          return (False, "API call failed during validation")
