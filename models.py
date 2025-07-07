# models.py
from sqlalchemy import Column, Integer, String, Text
from database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    step_type = Column(String)
    question = Column(Text)
    object = Column(String)
    user_ans = Column(Text)
    correct_ans = Column(Text)
    response = Column(Text)  # LLM's evaluation result
