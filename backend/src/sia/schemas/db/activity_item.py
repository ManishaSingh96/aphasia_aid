import uuid
from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field

from sia.schemas.db.activity_types import (
    FreeTextQuestionConfig,
    FreeTextQuestionEvaluationConfig,
)
from sia.schemas.db.enums import ActivityItemStatus, ActivityItemType

QuestionConfigUnion = Union[FreeTextQuestionConfig]
QuestionEvaluationConfigUnion = Union[FreeTextQuestionEvaluationConfig]


# base model with fields common to all Activity Items
class ActivityItemBase(BaseModel):
    activity_type: ActivityItemType
    activity_id: uuid.UUID
    max_retries: int = 2
    attempted_retries: int = 0
    status: ActivityItemStatus = ActivityItemStatus.NOT_TERMINATED


class ActivityItemCreate(ActivityItemBase):
    question_config: QuestionConfigUnion = Field(discriminator="activity_type")
    question_evaluation_config: QuestionEvaluationConfigUnion = Field(
        discriminator="activity_type",
    )


class ActivityItem(ActivityItemBase):
    id: uuid.UUID
    created_at: datetime
    question_config: QuestionConfigUnion = Field(discriminator="activity_type")
    question_evaluation_config: QuestionEvaluationConfigUnion = Field(
        discriminator="activity_type",
    )


# NOTE: This is not meant for db entires, more for application level
class ActivityItemCreateRelaxed(BaseModel):
    activity_type: ActivityItemType
    max_retries: int = 2
    question_config: QuestionConfigUnion = Field(discriminator="activity_type")
    question_evaluation_config: QuestionEvaluationConfigUnion = Field(
        discriminator="activity_type",
    )
