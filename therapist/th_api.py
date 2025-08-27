from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from therapist.model import generate_therapist
from typing import Dict
import asyncio
from time import time
router = APIRouter()
therapist = generate_therapist()

class PromptRequest(BaseModel):
    age:str
    gender:str
    location: str
    profession: str
    language: str
    severity:str

class EvalTestrequest(BaseModel):
    object: str


class ValidRequest(BaseModel):
    object: str
    question_type: str
    question: str
    user_response: str
    user_history: Dict[int, str] = {} 
    hint_history: Dict[int, str] = {}  
    

@router.post("/exercise_sets")
async def generate_exercise_sets(request: PromptRequest):
    try:
    
        loop = asyncio.get_event_loop()
        start=time()
        output = await loop.run_in_executor(
            None,
            lambda: therapist.main(
                request.age,
                request.gender,
                request.location,
                request.profession,
                request.language,
                request.severity,
            )
        )
        return {"response": output, "time": time()-start}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/validate_evaluator")
def evaluator_test(request: EvalTestrequest):
    """
    Evalutor testing 
    """
    try:
        output = therapist._testevaluator(
            request.object)

        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate_sets")
def validate_user_response(request: ValidRequest):
    """
    Validate user's answer against expected answer using therapist model logic.
    """
    try:
        output = therapist.evaluate(
            request.object,
            request.question,
            request.question_type,
            request.user_response,
            request.user_history,
            request.hint_history,  
        )
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
