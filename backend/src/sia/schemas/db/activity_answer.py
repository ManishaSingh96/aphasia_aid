import uuid
from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field

from sia.schemas.db.activity_types import FreeTextAnswer

AnswerUnion = Union[FreeTextAnswer]


class ActivityAnswerBase(BaseModel):
    activity_item_id: uuid.UUID
    is_correct: bool


class ActivityAnswerCreate(ActivityAnswerBase):
    answer: AnswerUnion = Field(discriminator="activity_type")


class ActivityAnswer(ActivityAnswerBase):
    answer: AnswerUnion = Field(discriminator="activity_type")
    id: uuid.UUID
    attempted_at: datetime
