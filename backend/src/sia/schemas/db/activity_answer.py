import uuid
from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field
from sia.schemas.db.activity_types import FreeTextAnswer
from sia.schemas.db.enums import ActivityItemType


class ActivityAnswerBase(BaseModel):
    activity_type: ActivityItemType
    activity_item_id: uuid.UUID
    skip: bool = False
    is_correct: bool = False

AnswerUnion = Union[FreeTextAnswer]

class ActivityAnswerCreate(ActivityAnswerBase):
    answer: AnswerUnion = Field(discriminator="activity_type")


class ActivityAnswer(ActivityAnswerBase):
    answer: AnswerUnion = Field(discriminator="activity_type")
    id: uuid.UUID
    attempted_at: datetime
