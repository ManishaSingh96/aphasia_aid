import uuid

from fastapi import Depends, Header, HTTPException, Request, status

from sia.db.connection import DatabaseClient
from sia.db.queries.user_queries import UserQueries
from sia.routers.dependencies.db import get_db_client
from sia.schemas.db.user_profile import Profile

TOKEN_PREFIX = "Bearer "  # noqa: S105 # nosec

db_client_dependency = Depends(get_db_client)


async def get_current_user(
    request: Request,
    db_client: DatabaseClient = db_client_dependency,
    authorization: str = Header(...),
) -> Profile:
    """Get the current user profile from the bearer token."""
    try:
        # Assuming the user_id is directly the bearer token value
        # e.g., Authorization: Bearer <user_id>
        if not authorization.startswith(TOKEN_PREFIX):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
        user_id_str = authorization[len(TOKEN_PREFIX) :]
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e

    user_queries = UserQueries(db_client)
    profile = await user_queries.get_profile_by_user_id(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    return profile
