from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from llm_call.llm import OpenAITextGenerator

router = APIRouter()
llm = OpenAITextGenerator()

class Message(BaseModel):
    role: str
    content: str

class PromptRequest(BaseModel):
    input_text: List[Message]

@router.post("/generate")
def generate_text(request: PromptRequest):
    try:
        # Forward input_text directly to OpenAI
        output = llm.generate(request.input_text)
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
