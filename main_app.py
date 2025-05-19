import openai
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("therapy.log"), 
        logging.StreamHandler()             
    ]
)
from generate_assistant import generate_assistant
from stt import speech_to_text

gs=generate_assistant(model="gpt-4o")
stt=speech_to_text()


def main():
    assistant_id,thread_id=gs._create_speech_assistant_()
    patient_id=str(gs.patient_info['patient_name'])+str(gs.patient_info['session_no'])
    logging.info("🧑‍⚕️ Starting your naming exercise session with the Speech Therapist!\n")
    with open(f"session_log_{patient_id}.txt", "w", encoding="utf-8") as log_file:
        response = gs.run_speech_session(assistant_id=assistant_id, thread_id=thread_id)
        log_file.write(f"🧑‍⚕️ Assistant: {response}\n")
        while True:
            # print("\n👤 You: ")
            user_msg = input("\n👤 You (press Enter to speak): ")
            if user_msg.strip() == "":
                logging.info("🎤 Recording audio for 5 seconds...")
                audio_data=stt.record_audio(duration=5)
                if audio_data is not None:
                    stt.save_audio(audio_data)
                user_msg = stt.transcribe_audio("input.wav")
            log_file.write(f"👤 You: {user_msg}\n")
            if user_msg.lower() in ["exit", "quit", "stop"]:
                print("🧑‍⚕️ Thank you for the session. Great job today!")
                break
            response=gs.run_speech_session(assistant_id=assistant_id, thread_id=thread_id, user_input=user_msg)
            log_file.write(f"🧑‍⚕️ Assistant: {response}\n")

if __name__ == "__main__":
    main()