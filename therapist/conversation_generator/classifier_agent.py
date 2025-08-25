import json
from therapist.utils import clean_json
from therapist.config import url
import httpx


class ClassifierAgent:
    def __init__(self):
        pass
    def evaluate_and_predict(self,patient_response):
        classifier_prompt = f"""
You are a **response classifier** assisting a **speech therapist** working with patients who have **aphasia**. Your job is to **classify the patient’s spoken response** as either **gibberish** or **non-gibberish**.

---

### Your Task:

Given a patient's response, **analyze** whether the spoken word is:

---

Non-gibberish:

The word is either:

-A real, meaningful word OR A plausible phonetic or misspelled form of a real word, including:
-Hindi words written phonetically in English (e.g., "jal", "dal", "pyaaj")
-Words with repeated letters or common transliteration mistakes (e.g., "phhal" → "phal", "khaal" → "khaali")
-Missed or swapped vowels/consonants (e.g., "reech" → "reach", "buk" → "book")

If the intended word is easily guessable based on sound and structure, classify it as non-gibberish.

Examples:
- "aalaarm" → "alarm"
- "phhal" → "phal"
- "buk" → "book"
- "pyaaj" → "pyaaz"
- "saan" → "sun"


#### **Gibberish**:
The word must be classified as **gibberish** if:

- It **cannot be clearly interpreted** as a real word,
- It does **not resemble** any known word in English or Hindi (or any widely spoken language),
- It contains **random, repeated, or unrelated syllables** (e.g., "aallaaa", "zqerp", "moofoo"),
- Any possible similarity is **too vague or speculative** to determine confidently,
- It is **too short** (e.g., "tu", "le", "ra", "bo") **and also does not match any known or meaningful Hindi/English word**.

**Important**: Words like “gol”, “tel”, “dal”, “kal”, etc. are short but **meaningful in Hindi**. These should be marked as **non-gibberish**.




### Evaluation Criteria:

1. **Compression Clarity**: Can a real word be clearly and confidently inferred?
2. **Phonetic Similarity**: Does the word sound like an actual word — not just vaguely?
3. **Linguistic Structure**: Does it follow any recognizable patterns from real words?
4. **Randomness/Nonsense Check**: Is it just a repetition of sounds or syllables with no clear meaning?

### Input:
Patient's spoken response: {patient_response}
### Output Format (strict JSON):

Return only a valid JSON dictionary like this — **no extra quotes or characters**:
{{"classification": true if gibberish/false if non gibberish, "reason": "Brief explanation here."}}

    """
        messages=[{"role": "user", "content": classifier_prompt}]

        response = httpx.post(
                url,
                json={"input_text": messages},
                timeout=60
            )
        response.raise_for_status()
        content = response.json()["response"]
        content=clean_json(content)
        decision_dict = json.loads(content)
        # print("classi",decision_dict)

        return decision_dict["classification"]
