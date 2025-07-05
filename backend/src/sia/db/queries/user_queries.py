import uuid
from dataclasses import dataclass
from typing import Optional

from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from sia.db.connection import DatabaseClient
from sia.db.queries.base_queries import BaseQueries
from sia.schemas.db.user_profile import PatientMetadata, Profile
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


@dataclass
class UserQueries(BaseQueries):
    """Provides methods for querying user profile data from the database."""

    GET_PROFILE_BY_USER_ID_SQL = (
        "SELECT user_id, metadata FROM profile WHERE user_id = %s"
    )
    UPDATE_PROFILE_SQL = """
        UPDATE profile
        SET metadata = %s
        WHERE user_id = %s
        RETURNING user_id, metadata
    """
    INSERT_PROFILE_SQL = """
        INSERT INTO profile (user_id, metadata)
        VALUES (%s, %s)
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
        """Update or create a user profile."""
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor(row_factory=class_row(Profile)) as cur:
                # Attempt to update first
                await cur.execute(
                    self.UPDATE_PROFILE_SQL,
                    (Jsonb(metadata.model_dump(mode="json")), user_id),
                )
                result = await cur.fetchone()

                if result:
                    return result
                else:
                    # If no rows were updated, the profile does not exist, so insert it
                    await cur.execute(
                        self.INSERT_PROFILE_SQL,
                        (user_id, Jsonb(metadata.model_dump(mode="json"))),
                    )
                    result = await cur.fetchone()
                    if result:
                        return result
                    raise Exception(
                        f"Failed to create or update profile for user_id {user_id}",
                    )

    async def check_user_exists(self, user_id: uuid.UUID) -> bool:
        """Check if a user with the given user_id exists in the auth.users table."""
        query = "SELECT EXISTS(SELECT 1 FROM auth.users WHERE id = %s)"
        async with self.db_client.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id,))
                result = await cur.fetchone()
                return result[0] if result else False
