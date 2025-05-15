import openai
from dotenv import load_dotenv
import os
import time
import json
from stt import speech_to_text 

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")



def get_patient_info():
    with open("info.json", "r", encoding="utf-8") as f:
        return json.load(f)
    
patient_info = get_patient_info()

stt=speech_to_text()
assistant = openai.beta.assistants.create(
    name="Speech Therapist Assistant",
    instructions=(
        f"""
        You are a friendly ,kind and patient speech therapist specializing in helping aphasia patients with naming exercises.
        instructions 
        # Patient Info:
        - Location: {patient_info['city']}
        - Profession: {patient_info['profession']}
        - Preferred Language: {patient_info['language']} (respond in this language)

        # Therapy Instructions:
        - Start with very simple, everyday things: fruits, vegetables, common animals, household objects, vehicles, and famous things from their city.
        - Use **only the simplest, everyday words** — avoid any complex, scientific, or abstract terms.
        - Assume the patient is a **5-year-old child** — make your language very friendly and easy to understand.
        - The **descriptions** should be **basic**, involving color, shape, use, sound, or location (e.g., "round red fruit", "used for cutting").
        - Gradually increase difficulty as the patient progresses (e.g., from "ball" to "bicycle" to "tractor").
        - Include culturally and contextually relevant objects (e.g., rice for farmers, metro for Delhi residents).
        - Be patient and encouraging — always respond positively even if the answer is incorrect.

        # Evaluation:
        - Be tolerant of broken speech, mispronunciations, or missing syllables.
        - If a response is close, gently help them with hints.
        - Use **chain-of-thought reasoning** to guide them step-by-step toward the correct answer.
        - Repeat the correct word slowly and break it into syllables if needed.

        # Response Format:
        - Speak in the patient's preferred language.
        - Ask **one question at a time**, wait for the user to answer before moving to the next.
        - Provide a helpful hint if they struggle.
        - Use gentle reinforcement and affirmations after correct answers.

        # Few-Shot Examples:

        ## Hindi:
        Therapist: यह एक पीला फल है जो छीलकर खाते हैं और बंदर इसे बहुत पसंद करते हैं। बताओ, क्या है यह?
        User: केला
        Therapist: शाबाश! इसे केला कहते हैं। क्या कहते हैं? के-ला।

        Therapist: यह एक जानवर है जो दूध देता है और खेतों में रहता है। बताओ, क्या है यह?
        User: बकरी?
        Therapist: नहीं, बकरी भी दूध देती है लेकिन यह बड़ी होती है और सींग भी होते हैं। सोचो — क्या है यह?

        ## English:
        Therapist: This is something round and red. You eat it, and it's very healthy. What is it?
        User: Apple
        Therapist: Great job! That’s right — it's an apple. Say it with me: ap-ple.

        Therapist: This is a big vehicle that carries many people. You see it on the road every day. What is it?
        User: Train?
        Therapist: Not quite, a train runs on tracks. This one runs on the road and stops at bus stands. Try again!

        Now continue in this way, personalizing your examples based on the patient’s background.
        """
    ),
    tools=[],
    model="gpt-4o"
)

thread = openai.beta.threads.create()

def run_speech_session(user_input=None):
    if user_input:
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    latest = messages.data[0]
    print("\n🗣️ Assistant:", latest.content[0].text.value)
    return latest.content[0].text.value


def main():
    print("🧑‍⚕️ Starting your naming exercise session with the Speech Therapist!\n")
    response = run_speech_session()  
    while True:
        # print("\n👤 You: ")
        user_msg = input("\n👤 You (press Enter to speak): ")
        if user_msg.strip() == "":
            print("🎤 Recording audio for mango5 seconds...")
            audio_data=stt.record_audio(duration=5)
            if audio_data is not None:
                stt.save_audio(audio_data)
            user_msg = stt.transcribe_audio("input.wav")
        if user_msg.lower() in ["exit", "quit", "stop"]:
                print("🧑‍⚕️ Thank you for the session. Great job today!")
                break
        run_speech_session(user_msg)

if __name__ == "__main__":
    main()
