from enum import StrEnum, auto


class ActivityStatus(StrEnum):
    IDLE = auto()
    ONGOING = auto()
    COMPLETED = auto()


class ActivityItemStatus(StrEnum):
    NOT_TERMINATED = auto()
    RETRIES_EXHAUST = auto()
    SKIP = auto()
    SUCCESS = auto()


class ActivityItemType(StrEnum):
    FREE_TEXT = auto()
