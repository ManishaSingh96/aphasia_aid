import uuid
from typing import Optional

from pydantic import BaseModel


class PatientMetadata(BaseModel):
    patient_name: str
    patient_age: str
    city: str
    language: str
    diagnosis: str

    # Optional fields
    patient_address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    education: Optional[str] = None


class Profile(BaseModel):
    user_id: uuid.UUID
    metadata: PatientMetadata
