import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from sia.db.connection import DatabaseClient
from sia.db.queries.user_queries import UserQueries
from sia.routers.dependencies.auth import get_current_user
from sia.routers.dependencies.db import get_db_client, get_user_queries
from sia.schemas.db.user_profile import PatientMetadata, Profile

# router = APIRouter(prefix="/profile", dependencies=[Depends(get_current_user)])
router = APIRouter(prefix="/profile")

# Define module-level variables for dependencies
current_user_dependency = Depends(get_current_user)  # auth
db_client_dependency = Depends(get_db_client)  # db
user_queries_dependency = Depends(get_user_queries)  # user queries


@router.post("/", response_model=Profile)
async def update_user_profile(
    updated_metadata: PatientMetadata,
    current_user: uuid.UUID = current_user_dependency,
    user_queries: UserQueries = user_queries_dependency,
) -> Profile:
    """Update the current user's profile."""
    try:
        updated_profile = await user_queries.update_profile(
            user_id=current_user,
            metadata=updated_metadata,
        )
        return updated_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        ) from e


@router.get("/", response_model=Profile)
async def get_user_profile(
    current_user: uuid.UUID = current_user_dependency,
    user_queries: UserQueries = user_queries_dependency,
) -> Profile:
    """Retrieve the current user's profile."""
    profile = await user_queries.get_profile_by_user_id(user_id=current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for the current user.",
        )
    return profile
