from therapist import generate_therapist
from stt import speech_to_text
import json
import re
import sys

gs = generate_therapist(model="gpt-4o")
stt=speech_to_text()
LOG_FILE="session_log.txt"
def log_interaction(question, user_response):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"Q: {question.strip()}\n")
        f.write(f"A: {user_response.strip()}\n\n")

def display_question_answer(prompt):
    print("\n🗣️ Assistant:", prompt)
    user_msg = input("\n👤 You (press Enter to speak): ")

    if user_msg.strip() == "":
        print("🎤 Recording audio for 5 seconds...")
        audio_data = stt.record_audio(duration=3)
        if audio_data is not None:
            stt.save_audio(audio_data)
            user_msg = stt.transcribe_audio("input.wav")
        else:
            print("⚠️ Audio recording failed. Please try again.")
            user_msg = ""

    check_for_exit(user_msg)
    log_interaction(prompt, user_msg)
    return user_msg

def clean_and_parse_json(response_text):
    cleaned = re.sub(r"^```(?:json|python)?\n?", "", response_text.strip())
    cleaned = re.sub(r"\n?```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("JSON parsing failed. Raw cleaned output:")
        print(cleaned)
        raise e
def check_for_exit(user_msg):
    if user_msg.lower().strip() in ["exit", "quit", "close", "stop"]:
        print("🧑‍⚕️ Thank you for the session. Great job today! 👋")
        sys.exit()

def main():
    exercise_sets = gs.call_question_generation_agent()

    for set in exercise_sets:
        print("\n🟢 Set ID:", set.get("set_id"))
        object_name = set.get("object")
        image_url = gs.call_image_generator_agent(object_name)

        for step in set["steps"]:
            question = step.get("question")
            user_msg = display_question_answer(question)
            eval = gs.call_evaluator_agent(object_name, user_msg, step)
            eval = clean_and_parse_json(eval)
            print("📝 Evaluation:", eval['assessment'])

            if eval['assessment'] == 'Correct':
                continue

            user_msg = display_question_answer(f"💡 {eval['feedback_hint']}")
            eval = gs.call_evaluator_agent(object_name, user_msg, step)
            eval = clean_and_parse_json(eval)
            print("📝 Evaluation:", eval['assessment'])

            if eval['assessment'] == 'Correct':
                continue

            user_msg = display_question_answer(f"💡 {eval['feedback_hint']}")
            eval = gs.call_evaluator_agent(object_name, user_msg, step)
            eval = clean_and_parse_json(eval)
            print("📝 Evaluation:", eval['assessment'])

            if eval['assessment'] == 'Correct':
                continue

            print(f"🖼️ चलिए, यह तस्वीर देखें: {image_url}")
            print("👉 अगले सवाल की ओर बढ़ते हैं...\n")

if __name__ == "__main__":
    main()
