from dataclasses import dataclass
from typing import List, Optional

from psycopg.rows import class_row

from sia.db.queries.base_queries import BaseQueries
from sia.schemas.db.models import (
    Car,
)
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


@dataclass
class CarQueries(BaseQueries):
    """Provides methods for querying car data from the database."""

    GET_CAR_BY_ID_SQL = "SELECT * FROM car WHERE id = %s"
    GET_ALL_CARS_SQL = "SELECT * FROM car ORDER BY created_at ASC"

    async def get_car_by_id(self, car_id: str) -> Optional[Car]:
        """Retrieve a car by its ID."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Car)) as cur:
                await cur.execute(self.GET_CAR_BY_ID_SQL, (car_id,))
                result = await cur.fetchone()
                return result

    async def get_all_cars(self) -> List[Car]:
        """Retrieve all cars from the database."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Car)) as cur:
                await cur.execute(self.GET_ALL_CARS_SQL)
                results: List[Car] = await cur.fetchall()
                return results

    async def get_all_cars_count(self) -> int:
        """Retrieve the total count of cars in the database."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM car")
                count = await cur.fetchone()
                return int(count[0]) if count else 0
