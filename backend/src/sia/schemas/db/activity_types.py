from typing import List, Literal

from pydantic import BaseModel


class BaseQuestionConfig(BaseModel):
    order: int = 0
    hints: List = []


class BaseQuestionEvaluationConfig(BaseModel):
    pass


class BaseAnswer(BaseModel):
    pass


class FreeTextAnswerHint(BaseModel):
    activity_type: Literal["FREE_TEXT"]


# -- Activity Type: FREE_TEXT
class FreeTextQuestionConfig(BaseQuestionConfig):
    activity_type: Literal["FREE_TEXT"]
    hints: List[FreeTextAnswerHint] = []
    prompt: str


class FreeTextQuestionEvaluationConfig(BaseQuestionEvaluationConfig):
    activity_type: Literal["FREE_TEXT"]
    expected_answer: str


class FreeTextAnswer(BaseAnswer):
    activity_type: Literal["FREE_TEXT"]
    text: str
