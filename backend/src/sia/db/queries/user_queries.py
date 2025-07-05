import uuid
from dataclasses import dataclass
from typing import Optional

from psycopg.rows import class_row

from sia.db.connection import DatabaseClient
from sia.db.queries.base_queries import BaseQueries
from sia.schemas.db.user_profile import PatientMetadata, Profile
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


@dataclass
class UserQueries(BaseQueries):
    """Provides methods for querying user profile data from the database."""

    GET_PROFILE_BY_USER_ID_SQL = (
        "SELECT user_id, metadata FROM user_profile WHERE user_id = %s"
    )
    UPDATE_PROFILE_SQL = """
        UPDATE user_profile
        SET metadata = %s
        WHERE user_id = %s
        RETURNING user_id, metadata
    """

    db_client: DatabaseClient

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> Optional[Profile]:
        """Retrieve a user profile by its user ID."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Profile)) as cur:
                await cur.execute(self.GET_PROFILE_BY_USER_ID_SQL, (user_id,))
                result = await cur.fetchone()
                return result

    async def update_profile(
        self,
        user_id: uuid.UUID,
        metadata: PatientMetadata,
    ) -> Profile:
        """Update the metadata of a user profile."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Profile)) as cur:
                await cur.execute(
                    self.UPDATE_PROFILE_SQL,
                    (metadata.model_dump_json(), user_id),
                )
                result = await cur.fetchone()
                if result:
                    return result
                raise ValueError(f"Profile with user_id {user_id} not found.")
