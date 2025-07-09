# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.database import Base  

class Interaction(Base):
    __tablename__ = "exercise_interactions"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    profession = Column(String)
    language = Column(String)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ValidationInteraction(Base):
    __tablename__ = "validation_interactions"
    id = Column(Integer, primary_key=True, index=True)
    step_type = Column(String)
    question = Column(Text)
    object = Column(String)
    user_ans = Column(String)
    correct_ans = Column(String)
    response = Column(Text)
    evaluation=Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
