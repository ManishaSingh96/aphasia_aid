from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, Field

from sia.schemas.db.activity_types import FreeTextAnswerHint
from sia.schemas.db.enums import ActivityItemType  # Renamed to avoid conflict

AnswerHintUninon = Union[FreeTextAnswerHint]


class AnswerResponse(BaseModel):
    activity_type: ActivityItemType
    next_item_id: Optional[str] = None
    success_verdict: bool
    activity_complete: bool
    hints: List[Annotated[AnswerHintUninon, Field(discriminator="activity_type")]] = []
