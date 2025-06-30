import uuid
from typing import List, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import class_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from sia.schemas.db.activity import Activity, ActivityCreate
from sia.schemas.db.activity_answer import ActivityAnswer, ActivityAnswerCreate
from sia.schemas.db.activity_item import (
    ActivityItem,
    ActivityItemCreateRelaxed,
)
from sia.schemas.db.enums import ActivityItemStatus, ActivityStatus
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


# NOTE: CreateActivityParams is the final output that our activity generation
# function creates. That function uses user info etc to prepare the activity
# params which we're storing here.
class CreateActivityParams(BaseModel):
    activity_create_params: ActivityCreate
    activity_items_create_params: List[ActivityItemCreateRelaxed]


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
            activity_type,
            question_config,
            question_evaluation_config
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
    """
    async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
        for item_params in activity_params.activity_items_create_params:
            await cur.execute(
                create_activity_item_sql,
                (
                    activity_result.id,
                    item_params.max_retries,
                    item_params.activity_type.value,
                    Jsonb(item_params.question_config.model_dump(mode="json")),
                    Jsonb(
                        item_params.question_evaluation_config.model_dump(mode="json"),
                    ),
                ),
            )

    return activity_result


async def update_activity_status(
    conn: AsyncConnection,
    activity_id: uuid.UUID,
    new_status: ActivityStatus,
) -> None:
    """Updates the status of a given activity."""
    update_sql = """
        UPDATE activity
        SET status = %s
        WHERE id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(update_sql, (new_status.value, activity_id))


async def update_activity_item_attempts_and_status(
    conn: AsyncConnection,
    activity_item_id: uuid.UUID,
    increment_attempts: bool = False,
    new_status: Optional[ActivityItemStatus] = None,
) -> None:
    """
    Updates 'attempted_tries' and optionally the 'status' of an activity item.
    Handles setting status to RETRIES_EXHAUST, SKIP, or SUCCESS.
    """
    update_clauses = []
    params = []

    if increment_attempts:
        update_clauses.append(sql.SQL("attempted_retries = attempted_retries + 1"))

    if new_status is not None:
        update_clauses.append(sql.SQL("status = %s"))
        params.append(new_status.value)

    if not update_clauses:
        logger.warning("No updates specified for activity item %s", activity_item_id)
        return

    set_clause = sql.SQL(", ").join(update_clauses)

    update_sql = sql.SQL("UPDATE activity_item SET {} WHERE id = %s;").format(
        set_clause,
    )
    params.append(activity_item_id)

    async with conn.cursor() as cur:
        await cur.execute(update_sql, tuple(params))


async def create_activity_answer(
    conn: AsyncConnection,
    answer_params: ActivityAnswerCreate,
) -> ActivityAnswer:
    """Inserts a new activity answer record."""
    create_sql = """
        INSERT INTO activity_answer (
            activity_item_id,
            answer,
            is_correct
        )
        VALUES (%s, %s, %s)
        RETURNING id, activity_item_id, answer, is_correct, attempted_at;
    """
    async with conn.cursor(row_factory=class_row(ActivityAnswer)) as cur:
        await cur.execute(
            create_sql,
            (
                answer_params.activity_item_id,
                Jsonb(answer_params.answer.model_dump(mode="json")),
                answer_params.is_correct,
            ),
        )
        result = await cur.fetchone()
        if not result:
            raise Exception("Failed to create activity answer")
        return result


GET_NEXT_NON_TERMINATED_ACTIVITY_ITEM_SQL = """
    SELECT * FROM activity_item
    WHERE activity_id = %s
    AND status = 'NOT_TERMINATED'
    ORDER BY (question_config->>'order')::int ASC
    LIMIT 1;
"""

GET_ACTIVITY_ITEM_BY_ID_IN_TRANSACTION_SQL = (
    "SELECT * FROM activity_item WHERE id = %s AND activity_id = %s"
)
GET_ACTIVITY_ITEMS_FOR_ACTIVITY_IN_TRANSACTION_SQL = (
    "SELECT * FROM activity_item WHERE activity_id = %s ORDER BY created_at ASC"
)


async def get_activity_item_in_transaction(
    conn: AsyncConnection,
    activity_item_id: uuid.UUID,
    activity_id: uuid.UUID,
) -> Optional[ActivityItem]:
    """Retrieve an activity item by its ID and associated activity ID within a transaction."""
    async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
        await cur.execute(
            GET_ACTIVITY_ITEM_BY_ID_IN_TRANSACTION_SQL,
            (
                activity_item_id,
                activity_id,
            ),
        )
        result = await cur.fetchone()
        return result


async def get_activity_items_for_activity_in_transaction(
    conn: AsyncConnection,
    activity_id: uuid.UUID,
) -> List[ActivityItem]:
    """Retrieve all activity items for a given activity ID within a transaction."""
    async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
        await cur.execute(
            GET_ACTIVITY_ITEMS_FOR_ACTIVITY_IN_TRANSACTION_SQL,
            (activity_id,),
        )
        results: List[ActivityItem] = await cur.fetchall()
        return results


async def get_next_non_terminated_activity_item(
    conn: AsyncConnection,
    activity_id: uuid.UUID,
) -> Optional[ActivityItem]:
    """
    Retrieves the next non-terminated activity item for a given activity,
    ordered by 'order' within its question_config JSONB.
    """
    async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
        await cur.execute(GET_NEXT_NON_TERMINATED_ACTIVITY_ITEM_SQL, (activity_id,))
        result = await cur.fetchone()
        return result
