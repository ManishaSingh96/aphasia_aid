import uuid
from typing import Optional

from fastapi import HTTPException, status
from psycopg import AsyncConnection

from sia.db.transactions.activity_transactions import (
    create_activity_answer,
    get_activity_item_in_transaction,
    get_activity_items_for_activity_in_transaction,
    get_next_non_terminated_activity_item,
    update_activity_item_attempts_and_status,
    update_activity_status,
)
from sia.schemas.api.answer_response import AnswerResponse
from sia.schemas.db.activity_answer import ActivityAnswerCreate
from sia.schemas.db.activity_item import ActivityItem
from sia.schemas.db.enums import ActivityItemStatus, ActivityItemType, ActivityStatus
from sia.telemetry.log import get_logger

logger = get_logger(__name__)


async def _determine_new_item_status(
    current_item: ActivityItem,
    is_correct: bool,
    skip: bool,
) -> Optional[ActivityItemStatus]:
    if skip:
        return ActivityItemStatus.SKIP
    elif is_correct:
        return ActivityItemStatus.SUCCESS
    elif current_item.attempted_retries >= current_item.max_retries:
        return ActivityItemStatus.RETRIES_EXHAUST
    return None  # Status remains NOT_TERMINATED


async def _check_activity_completion(
    conn: AsyncConnection,
    activity_id: uuid.UUID,
) -> bool:
    all_activity_items = await get_activity_items_for_activity_in_transaction(
        conn,
        activity_id,
    )
    return all(
        item.status
        in [
            ActivityItemStatus.RETRIES_EXHAUST,
            ActivityItemStatus.SKIP,
            ActivityItemStatus.SUCCESS,
        ]
        for item in all_activity_items
    )


async def _construct_response_data(
    conn: AsyncConnection,
    updated_item: ActivityItem,
    is_correct_answer: bool,
    activity_id: uuid.UUID,
    activity_completed: bool,
    activity_type: str,
) -> AnswerResponse:  # Return type remains AnswerResponse
    activity_type = ActivityItemType(activity_type)
    next_item_id = None
    if updated_item.status in [
        ActivityItemStatus.SKIP,
        ActivityItemStatus.SUCCESS,
    ]:
        next_non_terminated_item = await get_next_non_terminated_activity_item(
            conn,
            activity_id,
        )
        if next_non_terminated_item:
            next_item_id = str(next_non_terminated_item.id)

    hints = []
    if not is_correct_answer and updated_item.status in [
        ActivityItemStatus.NOT_TERMINATED,
        ActivityItemStatus.RETRIES_EXHAUST,
    ]:
        question_config = updated_item.question_config
        hints = question_config.hints

    # Construct the single AnswerResponse model
    return AnswerResponse(
        next_item_id=next_item_id,
        hints=hints,
        success_verdict=is_correct_answer,
        activity_complete=activity_completed,
        activity_type=activity_type,
    )


async def handle_submit_activity_item_answer(
    conn: AsyncConnection,
    activity_id: uuid.UUID,
    activity_item_id: uuid.UUID,
    answer_params: ActivityAnswerCreate,
) -> AnswerResponse:  # Return type remains AnswerResponse
    """Submits an answer for an activity item, updates its state, and checks for activity completion."""
    # 1. Retrieve Current ActivityItem
    activity_item = await get_activity_item_in_transaction(
        conn,
        activity_item_id,
        activity_id,
    )
    if not activity_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity item not found",
        )

    # Ensure the activity item belongs to the correct activity
    if activity_item.activity_id != activity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity item does not belong to the specified activity",
        )

    # 2. Pre-check for Terminal State
    if activity_item.status in [
        ActivityItemStatus.RETRIES_EXHAUST,
        ActivityItemStatus.SKIP,
        ActivityItemStatus.SUCCESS,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity item is already in a terminal state.",
        )

    initial_item_status = activity_item.status

    # 3. Increment attempted_tries
    await update_activity_item_attempts_and_status(
        conn,
        activity_item_id,
        increment_attempts=True,
    )

    # 4. Create ActivityAnswer Record
    await create_activity_answer(conn, answer_params)

    # 5. Determine New ActivityItem Status
    # Re-fetch ActivityItem to get updated attempted_tries
    updated_activity_item = await get_activity_item_in_transaction(
        conn,
        activity_item_id,
        activity_id,
    )
    if not updated_activity_item:
        # This should not happen if it was found initially
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated activity item.",
        )

    new_item_status = await _determine_new_item_status(
        updated_activity_item,
        answer_params.is_correct,
        answer_params.skip,
    )

    # 6. Update ActivityItem Status (if applicable)
    if new_item_status and new_item_status != initial_item_status:
        await update_activity_item_attempts_and_status(
            conn,
            activity_item_id,
            new_status=new_item_status,
        )
        # Update the local object to reflect the new status for subsequent checks
        updated_activity_item.status = new_item_status

    # 7. Check for Overall Activity Completion
    activity_completed = await _check_activity_completion(conn, activity_id)
    if activity_completed:
        await update_activity_status(conn, activity_id, ActivityStatus.COMPLETED)

    # 8. Construct Response
    response_data = await _construct_response_data(
        conn,
        updated_activity_item,
        answer_params.is_correct,
        activity_id,
        activity_completed,
        updated_activity_item.question_config.activity_type,  # Pass activity_type
    )

    return response_data
