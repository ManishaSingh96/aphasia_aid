from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from therapist.model import generate_therapist
from typing import Dict

router = APIRouter()
therapist = generate_therapist()

class PromptRequest(BaseModel):
    age:str
    gender:str
    lifestyle:str
    location: str
    profession: str
    language: str
    severity:str

class EvalTestrequest(BaseModel):
    object: str
    question: str
    question_type: str
    patient_response:str


class ValidRequest(BaseModel):
    object: str
    question_type: str
    question: str
    user_response: str
    user_history: Dict[int, str] = {} 
    hint_history: Dict[int, str] = {}  
    


@router.post("/exercise_sets")
def generate_exercise_sets(request: PromptRequest):
    """
    Generate therapist-based exercise sets based on patient profile
    """
    try:
        output = therapist.main(request.age,request.gender,request.lifestyle,request.location, request.profession, request.language,request.severity)

        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/validate_evaluator")
def evaluator_test(request: EvalTestrequest):
    """
    Evalutor testing 
    """
    try:
        output = therapist._testevaluator(
            request.object, request.question, request.question_type,request.patient_response)

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
