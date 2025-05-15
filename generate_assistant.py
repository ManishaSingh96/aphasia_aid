import openai
from dotenv import load_dotenv
import os
import time
import json 
from prompt import prompt


load_dotenv()

class generate_assistant:
    def __init__(self,model,assistant_name="Speech Therapist Assistant"):
        self.model=model
        self.prompt=prompt
        self.assistant_name=assistant_name

    def _create_speech_assistant_(self):

        openai.api_key = os.getenv("OPENAI_API_KEY")
        assistant = openai.beta.assistants.create(
        name=self.assistant_name,
        instructions=(self.prompt),
        tools=[],
        model=self.model
        )
        thread = openai.beta.threads.create()

        assistant_id=assistant.id
        thread_id=thread.id
        return assistant_id,thread_id
    
    def run_speech_session(self, assistant_id, thread_id, user_input=None):
        if user_input:
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
            )
        else:
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="assistant",
                content="Let's begin the therapy session. How are you feeling today?"
            )

        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        latest = messages.data[0]
        print("\n🗣️ Assistant:", latest.content[0].text.value)
        return latest.content[0].text.value
    