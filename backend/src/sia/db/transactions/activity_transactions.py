from typing import List

from psycopg import AsyncConnection
from psycopg.rows import class_row
from pydantic import BaseModel

from sia.schemas.db.activity import Activity, ActivityCreate
from sia.schemas.db.activity_item import ActivityItem, ActivityItemCreate
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


# NOTE: CreateActivityParams is the final output that our activity generation
# function creates. That function uses user info etc to prepare the activity
# params which we're storing here.
class CreateActivityParams(BaseModel):
    activity_create_params: ActivityCreate
    activity_items_create_params: List[ActivityItemCreate]


async def create_activity(
    conn: AsyncConnection,
    activity_params: CreateActivityParams,
) -> Activity:
    create_activity_sql = """
        INSERT INTO activity (user_id, status, generated_title)
        VALUES (%s, %s, %s)
        RETURNING id, user_id, status, generated_title, created_at;
    """
    async with conn.cursor(row_factory=class_row(Activity)) as cur:
        await cur.execute(
            create_activity_sql,
            (
                activity_params.activity_create_params.user_id,
                activity_params.activity_create_params.status.value,
                activity_params.activity_create_params.generated_title,
            ),
        )
        activity_result = await cur.fetchone()
        if not activity_result:
            raise Exception("Failed to create activity")

    create_activity_item_sql = """
        INSERT INTO activity_item (
            activity_id,
            max_retries,
            status,
            activity_type,
            question_config,
            question_evaluation_config
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
        for item_params in activity_params.activity_items_create_params:
            await cur.execute(
                create_activity_item_sql,
                (
                    activity_result.id,
                    item_params.max_retries,
                    item_params.status.value,
                    item_params.activity_type.value,
                    item_params.question_config.model_dump_json(),
                    item_params.question_evaluation_config.model_dump_json(),
                ),
            )

    return activity_result
