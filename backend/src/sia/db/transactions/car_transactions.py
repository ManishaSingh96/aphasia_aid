from typing import Optional

from psycopg import AsyncConnection
from psycopg.rows import class_row

from sia.schemas.db.models import (
    Car,
)
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


async def create_car(conn: AsyncConnection, car_data: Car) -> Optional[Car]:
    """Create a new car entry in the database within an existing transaction."""
    create_car_sql = """
    INSERT INTO car (id, owner_name)
    VALUES (%s, %s)
    RETURNING *
    """
    async with conn.cursor(row_factory=class_row(Car)) as cur:
        await cur.execute(
            create_car_sql,
            (
                car_data.id,
                car_data.owner_name,
            ),
        )
        result = await cur.fetchone()
        return result


async def update_car_color(
    conn: AsyncConnection,
    car_id: str,
    new_color: str,
) -> Optional[Car]:
    """Update the color of a car within an existing transaction."""
    update_car_color_sql = """
    UPDATE car
    SET color = %s
    WHERE id = %s
    RETURNING *
    """
    async with conn.cursor(row_factory=class_row(Car)) as cur:
        await cur.execute(update_car_color_sql, (new_color, car_id))
        result = await cur.fetchone()
        return result
