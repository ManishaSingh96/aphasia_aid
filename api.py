from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from generate_assistant import generate_assistant
from stt import speech_to_text
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("therapy.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI(title="Speech Therapy API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the assistant and speech-to-text
gs = generate_assistant(model="gpt-4o")
stt = speech_to_text()

# Store session data
sessions = {}

class SessionData(BaseModel):
    assistant_id: str
    thread_id: str

class Message(BaseModel):
    message: str

@app.post("/start_session")
async def start_session():
    """Start a new therapy session"""
    try:
        assistant_id, thread_id = gs._create_speech_assistant_()
        session_id = f"{assistant_id}_{thread_id}"
        sessions[session_id] = SessionData(assistant_id=assistant_id, thread_id=thread_id)
        
        # Get initial response
        response = gs.run_speech_session(
            assistant_id=assistant_id,
            thread_id=thread_id,
            user_input=None
        )
        
        return {
            "session_id": session_id,
            "message": response
        }
    except Exception as e:
        logging.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send_message/{session_id}")
async def send_message(session_id: str, message: Message):
    """Send a text message to the assistant"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = sessions[session_id]
        response = gs.run_speech_session(
            assistant_id=session.assistant_id,
            thread_id=session.thread_id,
            user_input=message.message
        )
        return {"message": response}
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send_audio/{session_id}")
async def send_audio(session_id: str, audio_file: UploadFile = File(...)):
    """Send an audio file for transcription and processing"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Save the uploaded audio file
        with open("input.wav", "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        # Transcribe the audio
        transcription = stt.transcribe_audio("input.wav")
        
        # Process the transcription
        session = sessions[session_id]
        response = gs.run_speech_session(
            assistant_id=session.assistant_id,
            thread_id=session.thread_id,
            user_input=transcription
        )
        
        return {
            "transcription": transcription,
            "response": response
        }
    except Exception as e:
        logging.error(f"Error processing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/end_session/{session_id}")
async def end_session(session_id: str):
    """End a therapy session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions.pop(session_id)
    return {"message": "Session ended successfully"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True) 