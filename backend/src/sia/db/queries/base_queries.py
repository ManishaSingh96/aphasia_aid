from abc import ABC
from dataclasses import dataclass
from typing import TypeVar

from sia.db.connection import DatabaseClient


@dataclass
class BaseQueries(ABC):
    """
    Abstract base class for all query classes.

    Ensures that a DatabaseClient is provided to all query implementations.
    """

    db_client: DatabaseClient


# Define a TypeVar for any class that inherits from BaseQueries
# This allows for type hinting functions that accept any query class
TDatabaseQuery = TypeVar("TDatabaseQuery", bound=BaseQueries)
