from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.database import SessionLocal, init_db
from backend.models import Interaction, ValidationInteraction
from sqlalchemy.orm import Session
import httpx, json

router = APIRouter()

# Therapist API URL
THERAPIST_EXERCISE_URL = "http://localhost:7878/api/exercise_sets"
THERAPIST_VALIDATE_URL = "http://localhost:7878/api/validate_sets"

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

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/exercise_sets")
def generate_exercise_sets(request: PromptRequest, db: Session = Depends(get_db)):
    try:
        response = httpx.post(THERAPIST_EXERCISE_URL, json=request.dict(),timeout=60)
        response.raise_for_status()
        result = response.json()
        db.add(Interaction(
            location=request.location,
            profession=request.profession,
            language=request.language,
            response=json.dumps(result, ensure_ascii=False)
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate_sets")
def validate_user_response(request: ValidRequest, db: Session = Depends(get_db)):
    try:
        response = httpx.post(THERAPIST_VALIDATE_URL, json=request.dict(),timeout=60)
        response.raise_for_status()
        result = response.json()

        db.add(ValidationInteraction(
            step_type=request.step_type,
            question=request.question,
            object=request.object,
            user_ans=request.user_ans,
            correct_ans=request.correct_ans,
            response=json.dumps(result, ensure_ascii=False)
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

