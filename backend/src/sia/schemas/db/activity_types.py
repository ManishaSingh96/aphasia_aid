from typing import List, Literal

from pydantic import BaseModel


class BaseHint(BaseModel):
    pass


class BaseQuestionConfig(BaseModel):
    order: int = 0
    hints: List[BaseHint] = []


class BaseQuestionEvaluationConfig(BaseModel):
    pass

class BaseAnswer(BaseModel):
    pass

class BaseAnswerResponse(BaseModel):
    hints: List[BaseHint] = []
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


class FreeTextAnswerResponse(BaseAnswerResponse):
    activity_type: Literal["FREE_TEXT"]
