import uuid
from datetime import datetime

from pydantic import BaseModel

from sia.schemas.db.enums import ActivityStatus

# -- Activity


class ActivityBase(BaseModel):
    user_id: uuid.UUID
    status: ActivityStatus = ActivityStatus.IDLE
    generated_title: str | None = None


class ActivityCreate(ActivityBase):
    pass


class Activity(ActivityBase):
    id: uuid.UUID
    created_at: datetime
