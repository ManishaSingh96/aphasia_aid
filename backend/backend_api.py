from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from backend.database import SessionLocal, init_db
from backend.models import ExerciseInteraction, ValidationInteraction
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
import json
import httpx, json


router = APIRouter()

# Therapist API URL
THERAPIST_EXERCISE_URL = "http://localhost:7878/api/exercise_sets"
THERAPIST_VALIDATE_URL = "http://localhost:7878/api/validate_sets"

class PromptRequest(BaseModel):
    age:str
    gender:str
    location: str
    profession: str
    language: str
    severity: str


class ValidRequest(BaseModel):
    question_id: str
    object: str
    question_type: str
    question: str
    user_response: str
    

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return {int(k): v for k, v in json.loads(value).items()}
    except Exception:
        return {}

def get_latest_validation(db: Session, question_id: str):
    row = (
        db.query(ValidationInteraction)
        .filter(ValidationInteraction.question_id == question_id)  # filter by session
        .order_by(desc(ValidationInteraction.id))
        .first()
    )
    if not row:
        return None

    return {
        "id": row.id,
        "session_id": question_id,
        "object": row.object,
        "question": row.question,
        "question_type": row.question_type,
        "user_history": _as_dict(row.user_history),
        "hint_history": _as_dict(row.hint_history),
        "created_at": str(getattr(row, "created_at", "")),
    }

@router.post("/exercise_sets")
def generate_exercise_sets(request: PromptRequest, db: Session = Depends(get_db)):
    try:
        response = httpx.post(THERAPIST_EXERCISE_URL, json=request.dict(),timeout=60)
        response.raise_for_status()
        result = response.json()
        db.add(ExerciseInteraction(
            age=request.age,
            gender=request.gender,
            location=request.location,
            profession=request.profession,
            language=request.language,
            severity=request.severity,
            response=json.dumps(result, ensure_ascii=False)
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_sets")
def validate_user_response(request: ValidRequest, db: Session = Depends(get_db)):
    try:
        latest_data = get_latest_validation(db,request.question_id)
        if latest_data:
            print(latest_data["user_history"])
            print(latest_data["hint_history"])
            user_history=latest_data["user_history"]
            hint_history=latest_data["hint_history"]
        else:
            user_history={}
            hint_history={}
        payload={
        "question_id":request.question_id,
        "object":request.object,
        "question_type":request.question_type,
        "question":request.question,
        "user_response":request.user_response,
        "user_history":user_history,
        "hint_history":hint_history
        }

        response = httpx.post(THERAPIST_VALIDATE_URL, json=payload,timeout=60)
        response.raise_for_status()
        result = response.json()

        db.add(ValidationInteraction(
            question_id=request.question_id,
            object=request.object,
            question=request.question,
            question_type=request.question_type,
            user_response=request.user_response,
            user_history=json.dumps(result["response"]["user_history"], ensure_ascii=False),
            hint_history=json.dumps(result["response"]["hint_history"], ensure_ascii=False),
            hint=json.dumps(result["response"]["hint"], ensure_ascii=False)
        ))

        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

