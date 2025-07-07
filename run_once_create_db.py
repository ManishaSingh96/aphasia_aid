# run_once_create_db.py
from database import Base, engine
from models import Interaction

Base.metadata.create_all(bind=engine)
