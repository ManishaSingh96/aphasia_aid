# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.database import Base  

class ExerciseInteraction(Base):
    __tablename__ = "exercise_interactions"
    id = Column(Integer, primary_key=True, index=True)
    
    location = Column(String)
    profession = Column(String)
    language = Column(String)
    severity=Column(String)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ValidationInteraction(Base):
    __tablename__ = "validation_interactions"
    id = Column(Integer, primary_key=True, index=True)
    question_id=Column(String)
    object = Column(String)
    question = Column(Text)
    question_type = Column(String)
    user_response = Column(String)
    user_history = Column(String)
    hint_history = Column(Text)
    hint=Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
