from typing import Literal

from pydantic import BaseModel


class BaseQuestionConfig(BaseModel):
    pass


class BaseQuestionEvaluationConfig(BaseModel):
    pass


class BaseAnswer(BaseModel):
    pass


# -- Activity Type: FREE_TEXT
class FreeTextQuestionConfig(BaseQuestionConfig):
    activity_type: Literal["FREE_TEXT"]
    prompt: str


class FreeTextQuestionEvaluationConfig(BaseQuestionEvaluationConfig):
    activity_type: Literal["FREE_TEXT"]
    expected_answer: str


class FreeTextAnswer(BaseAnswer):
    activity_type: Literal["FREE_TEXT"]
    text: str
