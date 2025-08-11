# run_once_create_db.py
from backend.database import Base, engine
from backend.models import ExerciseInteraction,QuestionInteraction,ValidationInteraction

Base.metadata.create_all(bind=engine)
