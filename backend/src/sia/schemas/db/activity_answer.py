import uuid
from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field

from sia.schemas.db.activity_types import FreeTextAnswer


class ActivityAnswerBase(BaseModel):
    # activity_type: ActivityItemType
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
