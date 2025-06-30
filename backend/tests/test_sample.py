import pytest
from test_helpers.test_queries_model import TestQueries

from sia.db.connection import DatabaseClient
from sia.db.transactions.car_transactions import create_car
from sia.schemas.db.models import Car


@pytest.mark.asyncio
async def test_car_creation_and_count(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
) -> None:
    """Test car creation and count using car queries."""
    client, query = test_db_client_w_test_db

    # Access car_queries directly from the TestQueries model
    car_queries = query.car

    # Create a new car instance
    new_car = Car(id="test_car_1", owner_name="John Doe")

    # Insert the car using the transaction function
    async with client.pool.connection() as conn:
        created_car = await create_car(conn, new_car)

    assert created_car is not None  # noqa: S101
    assert created_car.owner_name == "John Doe"  # noqa: S101

    # Check the count of cars
    count = await car_queries.get_all_cars_count()
    assert count == 1  # noqa: S101


def test_sample_function(sample_fixture: str) -> None:
    """A sample test function that uses a fixture."""
    # S101: For simple equality checks, assert is idiomatic.
    # For more complex scenarios, pytest's assertion helpers might be preferred.
    assert sample_fixture == "sample_data"  # noqa: S101
