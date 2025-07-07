from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from therapist.model import generate_therapist
from database import SessionLocal
from models import Interaction

router = APIRouter()
therapist = generate_therapist()

class PromptRequest(BaseModel):
    location: str
    profession: str
    language: str

class ValidRequest(BaseModel):
    step_type: str
    question: str
    object: str
    user_ans: str
    correct_ans: str

@router.post("/exercise_sets")
def generate_exercise_sets(request: PromptRequest):
    """
    Generate therapist-based exercise sets based on location, profession, and language.
    """
    try:
        output = therapist.main(request.location, request.profession, request.language)
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
            request.step_type,
            request.question,
            request.object,
            request.user_ans,
            request.correct_ans
        )
        db = SessionLocal()
        interaction = Interaction(
            step_type=request.step_type,
            question=request.question,
            object=request.object,
            user_ans=request.user_ans,
            correct_ans=request.correct_ans,
            response=output['feedback_hint'])
        db.add(interaction)
        db.commit()
        db.close()
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
