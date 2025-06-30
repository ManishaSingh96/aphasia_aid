from enum import Enum


class ActivityStatus(str, Enum):
    IDLE = "IDLE"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class ActivityItemStatus(str, Enum):
    NOT_TERMINATED = "NOT_TERMINATED"
    RETRIES_EXHAUST = "RETRIES_EXHAUST"
    SKIP = "SKIP"
    SUCCESS = "SUCCESS"


class ActivityItemType(str, Enum):
    FREE_TEXT = "FREE_TEXT"
