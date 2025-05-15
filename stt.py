import os
import scipy.io.wavfile as wav
from openai import OpenAI
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()


class speech_to_text:
    def __init__(self, sample_rate=16000):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sample_rate=16000

    def record_audio(self,duration=15):
        try:
            audio_data = sd.rec(int(duration * self.sample_rate), 
                                samplerate=self.sample_rate, 
                                channels=1,
                                dtype='float32')
            sd.wait()
            return audio_data
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None

    def save_audio(self,audio_data, filename="input.wav"):   
        try:
            wav.write(filename, self.sample_rate, audio_data)
            print(f"Audio saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False

    def transcribe_audio(self,audio_file_path):
        with open("input.wav", "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="hi"
        )
        print("input:",transcript.text)
        return transcript.text