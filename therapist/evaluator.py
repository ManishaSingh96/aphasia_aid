import openai
import os

class EvaluatorAgent:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def evaluate_and_predict(self, question,question_type,patient_response):
        system_prompt = f"""
    You are a speech therapy assistant helping patients with aphasia.
    You will be given:
    - A question posed to the patient :{question}
    - a question type:{question_type}
    - The patient's response:{patient_response}

    Your task is to:
    1. **Evaluate** whether the patient has understood and/or spoken the object correctly.
    2. Based on that, **predict the next best step** using these rules:

    - Give a descriptive hint → if the response is incorrect and the patient is struggling to understand the object.
    - Give a phonetic hint → if the response is incorrect and the patient understands but struggles to say the word.
    - Move on to the next question → if the patient responded the correct word successfully.
    - If the response is **not the expected answer but still valid in context** (e.g., “चटाई” instead of “कुर्सी”) → treat it as **correct** and note that in the evaluation

    3.Return the next step as one of thefollowing string only (Descriptive Hint,Phoentic Hint,Next question)

    Here are a few examples:

    Example 1:
    Question: तुम दाँत साफ़ करने के लिए क्या इस्तेमाल करते हो?
    Patient Response: साबुन...?
    Evaluation: गलत जवाब। मरीज वस्तु को पहचान नहीं पा रहा है।
    Next Step: Descriptive Hint

    Example 2:
    Question: तुम सब्ज़ियाँ काटने के लिए क्या इस्तेमाल करते हो?
    Patient Response: च...च...क-...
    Evaluation: गलत जवाब। मरीज वस्तु को पहचानता है लेकिन नाम बोलने में कठिनाई हो रही है।
    Next Step: Phoentic Hint

    Example 3:
    Question: बाहर जाने से पहले तुम पैरों में क्या पहनते हो?
    Patient Response: जूते।
    Evaluation: सही जवाब।
    Next Step: Next Question

    ### Output Format for each question:

    Return your output in  a json format -- no strings, no markdown, no lists.

    with the folllowing keys
    "Question": "<Hindi question>" ,
    "Patient Response":"<patient response>",
    "Evaluation":"<evaluation>",
    "Next Step":"<next step>"
    
    """

        # user_input = f"Question: {question.strip()}\nPatient Response: {patient_response.strip()}"

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt}
                
            ]
        )

        return response['choices'][0]['message']['content'].strip()
    # Example 4:
    # Question: बाहर जाने से पहले तुम पैरों में क्या पहनते हो?
    # Patient Response: जूते।
    # Evaluation: मरीज ने सही तरीके से दोहराव पूरा किया।
    # Next Step: Move on to the next question: धूप से बचने के लिए सिर पर क्या पहनते हो?