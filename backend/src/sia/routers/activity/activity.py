import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from sia.db.connection import DatabaseClient
from sia.db.queries.activity_queries import ActivityQueries
from sia.db.transactions.activity_transactions import (
    CreateActivityParams,
    create_activity,
    get_next_non_terminated_activity_item,
    update_activity_status,
)
from sia.routers.activity.answer_handler import handle_submit_activity_item_answer
from sia.routers.dependencies.auth import get_current_user
from sia.routers.dependencies.db import get_activity_queries, get_db_client
from sia.schemas.api.answer_response import AnswerResponse
from sia.schemas.db.activity import Activity, FullActivityDetails
from sia.schemas.db.activity_answer import ActivityAnswer, ActivityAnswerCreate
from sia.schemas.db.activity_item import ActivityItem, ActivityItemCreateRelaxed
from sia.schemas.db.enums import ActivityStatus
from sia.telemetry.log import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/activities",
    dependencies=[Depends(get_current_user)],
)  # This one is fine as it's not a default argument

# Define module-level variables for dependencies
activity_queries_dependency = Depends(get_activity_queries)
db_client_dependency = Depends(get_db_client)
current_user_dependency = Depends(get_current_user)


# Dummy remote endpoint call for activity generation
async def dummy_call_remote_activity_generation_endpoint(
    user_id: uuid.UUID,
) -> CreateActivityParams:
    # This is a placeholder for the actual remote call
    # For now, return dummy data
    from sia.schemas.db.activity import ActivityCreate
    from sia.schemas.db.activity_item import ActivityItemType
    from sia.schemas.db.activity_types import (
        FreeTextQuestionConfig,
        FreeTextQuestionEvaluationConfig,
    )

    dummy_activity_create = ActivityCreate(
        user_id=user_id,
        status=ActivityStatus.IDLE,
        generated_title="Dummy Generated Activity",
    )
    dummy_activity_items_create = [
        ActivityItemCreateRelaxed(
            activity_type=ActivityItemType.FREE_TEXT,
            question_config=FreeTextQuestionConfig(
                activity_type=ActivityItemType.FREE_TEXT,
                prompt="What is the capital of France?",
            ),
            question_evaluation_config=FreeTextQuestionEvaluationConfig(
                activity_type=ActivityItemType.FREE_TEXT,
                expected_answer="Paris",
            ),
        ),
        ActivityItemCreateRelaxed(
            activity_type=ActivityItemType.FREE_TEXT,
            question_config=FreeTextQuestionConfig(
                activity_type=ActivityItemType.FREE_TEXT,
                prompt="What is 2+2?",
            ),
            question_evaluation_config=FreeTextQuestionEvaluationConfig(
                activity_type=ActivityItemType.FREE_TEXT,
                expected_answer="4",
            ),
        ),
    ]
    return CreateActivityParams(
        activity_create_params=dummy_activity_create,
        activity_items_create_params=dummy_activity_items_create,
    )


@router.get("/", response_model=List[Activity])
async def list_activities(
    current_user: uuid.UUID = current_user_dependency,
    activity_queries: ActivityQueries = activity_queries_dependency,
) -> List[Activity]:
    """List all activities for the user."""
    activities: List[Activity] = await activity_queries.get_all_activities_of_user(
        current_user,
    )
    return activities


@router.get("/{activity_id}/details", response_model=FullActivityDetails)
async def get_activity_details(
    activity_id: uuid.UUID,
    activity_queries: ActivityQueries = activity_queries_dependency,
) -> FullActivityDetails:
    """Gets info about individual activity, including related activity items and answers."""
    (
        activity,
        activity_items,
        activity_answers,
    ) = await activity_queries.get_activity_with_details_by_id(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    # Return all three components as a FullActivityDetails object
    return FullActivityDetails(
        activity=activity,
        activity_items=activity_items,
        activity_answers=activity_answers,
    )


@router.get(
    "/{activity_id}/items/{activity_item_id}",
    response_model=ActivityItem,
)
async def get_activity_item(
    activity_id: uuid.UUID,
    activity_item_id: uuid.UUID,
    activity_queries: ActivityQueries = activity_queries_dependency,
) -> ActivityItem:
    """Gets an activity item."""
    activity_item = await activity_queries.get_activity_item_by_id(
        activity_id,
        activity_item_id,
    )
    if not activity_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity item not found",
        )
    return activity_item


# TODO: 1. Profile specific generation, also take in context that'll be helpful
# for the ai to generate the questions
@router.post("/create", response_model=Activity)
async def create_new_activity(
    current_user: uuid.UUID = current_user_dependency,
    db_client: DatabaseClient = db_client_dependency,
) -> Activity:
    """
    Creates a new activity by calling a remote endpoint to generate activity parameters,
    then stores the activity and its items in a transaction.
    """
    activity_params = await dummy_call_remote_activity_generation_endpoint(
        current_user,
    )
    async with db_client.pool.connection() as conn:
        created_activity = await create_activity(conn, activity_params)
    return created_activity


@router.post("/{activity_id}/start", response_model=ActivityItem)
async def start_activity(
    activity_id: uuid.UUID,
    current_user: uuid.UUID = current_user_dependency,
    db_client: DatabaseClient = db_client_dependency,
    activity_queries: ActivityQueries = activity_queries_dependency,
) -> ActivityItem:
    """
    Starts an activity by setting its status to ONGOING and returns the first
    non-terminated activity item.
    """
    async with db_client.pool.connection() as conn:
        activity = await activity_queries.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        if activity.user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this activity",
            )

        if activity.status == ActivityStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity is already completed",
            )

        # Update activity status to ONGOING
        await update_activity_status(conn, activity_id, ActivityStatus.ONGOING)

        # Get the next non-terminated activity item
        next_item = await get_next_non_terminated_activity_item(conn, activity_id)
        if not next_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid activity items found to start.",
            )

        # Optionally, update the status of the first item to ONGOING if needed,
        # though NOT_TERMINATED might be sufficient for initial state.
        # For now, we assume NOT_TERMINATED is the "ongoing" state for items.
        # If a specific "ONGOING" status for items is needed, it should be added to enum.

        return next_item


@router.post("/{activity_id}/items/{activity_item_id}/answer")
async def submit_activity_item_answer(
    activity_id: uuid.UUID,
    activity_item_id: uuid.UUID,
    answer_params: ActivityAnswerCreate,
    current_user: uuid.UUID = current_user_dependency,
    db_client: DatabaseClient = db_client_dependency,
) -> AnswerResponse:
    """Submits an answer for an activity item, updates its state, and checks for activity completion."""
    async with db_client.pool.connection() as conn:
        response_data: AnswerResponse = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            activity_item_id,
            answer_params,
        )
    return response_data
