import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ActivityStatus(StrEnum):
    IDLE = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()

class ActivityItemType(StrEnum):
    MULTIPLE_CHOICE = auto()
    FREE_TEXT = auto()

#
# Activity
#

class ActivityBase(BaseModel):
    """Fields provided by the user when creating an activity."""

    user_id: uuid.UUID
    status: ActivityStatus
    generated_title: Optional[str] = None

class ActivityCreate(ActivityBase):
    """Model for creating a new activity."""

    pass

class Activity(ActivityBase):
    """Model representing a complete activity record from the database."""

    id: uuid.UUID
    created_at: datetime


#
# ActivityItem
#

class ActivityItemBase(BaseModel):
    """Fields provided by the user when creating an activity item."""

    activity_id: uuid.UUID
    activity_type: ActivityItemType
    prompt_config: Dict[str, Any]
    evaluation_config: Dict[str, Any]

class ActivityItemCreate(ActivityItemBase):
    """Model for creating a new activity item."""

    pass

class ActivityItem(ActivityItemBase):
    """Model representing a complete activity_item record from the database."""

    id: uuid.UUID
    created_at: datetime

#
# ActivityAnswer
#

class ActivityAnswerBase(BaseModel):
    """Fields provided by the user when submitting an answer for an activity item."""

    activity_item_id: uuid.UUID
    response_data: Dict[str, Any]
    accuracy_score: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    is_correct: bool


class ActivityAnswerCreate(ActivityAnswerBase):
    """Model for creating a new answer record."""

    pass


class ActivityAnswer(ActivityAnswerBase):
    """Model representing a complete answer record from the database."""

    id: uuid.UUID
    attempted_at: datetime # Keeping the field name 'attempted_at' to match the DB column
