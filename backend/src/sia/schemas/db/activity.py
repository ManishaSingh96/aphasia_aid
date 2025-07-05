import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel

from sia.schemas.db.activity_answer import ActivityAnswer
from sia.schemas.db.activity_item import ActivityItem
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


class FullActivityDetails(BaseModel):
    activity: Activity
    activity_items: List[ActivityItem]
    activity_answers: List[ActivityAnswer]
