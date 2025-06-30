from pydantic import BaseModel, ConfigDict

from sia.db.queries.car_queries import CarQueries


class TestQueries(BaseModel):
    """
    A Pydantic model to hold various query instances for testing.

    This provides better type hinting and discoverability for query objects
    passed through fixtures.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    car: CarQueries
