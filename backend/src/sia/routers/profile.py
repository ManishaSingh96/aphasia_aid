from fastapi import APIRouter, Depends, HTTPException, status

from sia.db.connection import DatabaseClient
from sia.db.queries.user_queries import UserQueries
from sia.routers.dependencies.auth import get_current_user
from sia.routers.dependencies.db import get_db_client
from sia.schemas.db.user_profile import PatientMetadata, Profile

router = APIRouter(prefix="/profile", dependencies=[Depends(get_current_user)])

# Define module-level variables for dependencies
current_user_dependency = Depends(get_current_user)
db_client_dependency = Depends(get_db_client)


@router.put("/", response_model=Profile)
async def update_user_profile(
    updated_metadata: PatientMetadata,
    current_user: Profile = current_user_dependency,
    db_client: DatabaseClient = db_client_dependency,
) -> Profile:
    """Update the current user's profile."""
    user_queries = UserQueries(db_client)
    try:
        updated_profile = await user_queries.update_profile(
            user_id=current_user.user_id,
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
