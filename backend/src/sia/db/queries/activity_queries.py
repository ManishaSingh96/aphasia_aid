import uuid
from dataclasses import dataclass
from typing import List, Optional

from psycopg.rows import class_row

from sia.db.queries.base_queries import BaseQueries
from sia.schemas.db.activity import Activity
from sia.schemas.db.activity_answer import ActivityAnswer
from sia.schemas.db.activity_item import ActivityItem
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


@dataclass
class ActivityQueries(BaseQueries):
    """Provides methods for querying activity data from the database."""

    GET_ACTIVITY_BY_ID_SQL = "SELECT * FROM activity WHERE id = %s"
    GET_ALL_ACTIVITIES_OF_USER_SQL = (
        "SELECT * FROM activity WHERE user_id = %s ORDER BY created_at DESC"
    )
    GET_ACTIVITY_ITEM_BY_ID_SQL = (
        "SELECT * FROM activity_item WHERE id = %s AND activity_id = %s"
    )
    GET_ACTIVITY_ITEMS_FOR_ACTIVITY_SQL = (
        "SELECT * FROM activity_item WHERE activity_id = %s ORDER BY created_at ASC"
    )
    GET_ACTIVITY_ANSWERS_FOR_ACTIVITY_ITEM_SQL = "SELECT * FROM activity_answer WHERE activity_item_id = %s ORDER BY attempted_at ASC"

    async def get_activity_by_id(self, activity_id: uuid.UUID) -> Optional[Activity]:
        """Retrieve an activity by its ID."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Activity)) as cur:
                await cur.execute(self.GET_ACTIVITY_BY_ID_SQL, (activity_id,))
                result = await cur.fetchone()
                return result

    async def get_all_activities_of_user(self, user_id: uuid.UUID) -> List[Activity]:
        """Retrieve all activities for a given user ID."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Activity)) as cur:
                await cur.execute(self.GET_ALL_ACTIVITIES_OF_USER_SQL, (user_id,))
                results: List[Activity] = await cur.fetchall()
                return results

    async def get_activity_item_by_id(
        self,
        activity_id: uuid.UUID,
        activity_item_id: uuid.UUID,
    ) -> Optional[ActivityItem]:
        """Retrieve an activity item by its ID and associated activity ID."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(ActivityItem)) as cur:
                await cur.execute(
                    self.GET_ACTIVITY_ITEM_BY_ID_SQL,
                    (
                        activity_item_id,
                        activity_id,
                    ),
                )
                result = await cur.fetchone()
                return result

    async def get_activity_with_details_by_id(
        self,
        activity_id: uuid.UUID,
    ) -> tuple[Optional[Activity], List[ActivityItem], List[ActivityAnswer]]:
        """Retrieve an activity along with its items and answers."""
        activity = await self.get_activity_by_id(activity_id)
        if not activity:
            return None, [], []

        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(ActivityItem)) as cur_items:
                await cur_items.execute(
                    self.GET_ACTIVITY_ITEMS_FOR_ACTIVITY_SQL,
                    (activity_id,),
                )
                activity_items: List[ActivityItem] = await cur_items.fetchall()

            all_activity_answers: List[ActivityAnswer] = []
            for item in activity_items:
                async with conn.cursor(
                    row_factory=class_row(ActivityAnswer),
                ) as cur_answers:
                    await cur_answers.execute(
                        self.GET_ACTIVITY_ANSWERS_FOR_ACTIVITY_ITEM_SQL,
                        (item.id,),
                    )
                    answers_for_item: List[ActivityAnswer] = (
                        await cur_answers.fetchall()
                    )
                    all_activity_answers.extend(answers_for_item)

        return activity, activity_items, all_activity_answers
