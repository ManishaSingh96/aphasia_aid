import uuid

import pytest
from fastapi import HTTPException, status
from test_helpers.test_queries_model import TestQueries

from sia.db.connection import DatabaseClient
from sia.db.transactions.activity_transactions import (
    CreateActivityParams,
    create_activity,
    get_activity_item_in_transaction,
    get_activity_items_for_activity_in_transaction,  # Added import
    update_activity_item_attempts_and_status,
)
from sia.routers.answer_handler import handle_submit_activity_item_answer
from sia.schemas.db.activity import ActivityCreate
from sia.schemas.db.activity_answer import ActivityAnswerCreate
from sia.schemas.db.activity_item import ActivityItemCreateRelaxed
from sia.schemas.db.activity_types import (
    FreeTextAnswer,  # Added import
    FreeTextAnswerHint,  # Added import
    FreeTextQuestionConfig,
    FreeTextQuestionEvaluationConfig,
)
from sia.schemas.db.enums import ActivityItemStatus, ActivityItemType, ActivityStatus
from sia.schemas.db.user import User


async def _create_test_activity_and_items(
    db_client: DatabaseClient,
    user: User,
    num_items: int = 1,
    max_retries_per_item: int = 3,
    initial_item_status: ActivityItemStatus = ActivityItemStatus.NOT_TERMINATED,
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    activity_items_create_params = []
    for i in range(num_items):
        question_config = FreeTextQuestionConfig(
            order=i,
            activity_type=ActivityItemType.FREE_TEXT,  # Changed from Literal to Enum
            prompt=f"Question {i + 1}?",
            hints=(
                [FreeTextAnswerHint(activity_type=ActivityItemType.FREE_TEXT)]
                if i == 0
                else []
            ),  # Changed to FreeTextAnswerHint objects
        )
        question_evaluation_config = FreeTextQuestionEvaluationConfig(
            activity_type=ActivityItemType.FREE_TEXT,
            expected_answer=f"Answer {i + 1}",
        )
        activity_items_create_params.append(
            ActivityItemCreateRelaxed(
                max_retries=max_retries_per_item,
                activity_type=ActivityItemType.FREE_TEXT,
                question_config=question_config,
                question_evaluation_config=question_evaluation_config,
            ),
        )

    activity_create_params = ActivityCreate(
        user_id=user.id,
        status=ActivityStatus.IDLE,
        generated_title="Test Activity",
    )

    create_activity_params = CreateActivityParams(
        activity_create_params=activity_create_params,
        activity_items_create_params=activity_items_create_params,
    )

    async with db_client.pool.connection() as conn:
        created_activity = await create_activity(conn, create_activity_params)
        activity_items = await get_activity_items_for_activity_in_transaction(
            conn,
            activity_id=created_activity.id,
        )
        item_ids = [item.id for item in activity_items]

        # Update initial status if needed
        if initial_item_status != ActivityItemStatus.NOT_TERMINATED:
            for item_id in item_ids:
                await update_activity_item_attempts_and_status(
                    conn,
                    item_id,
                    new_status=initial_item_status,
                )

    return created_activity.id, item_ids


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_success(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, queries = test_db_client_w_test_db
    user = create_user
    activity_id, item_ids = await _create_test_activity_and_items(
        db_client,
        user,
        num_items=2,
    )
    first_item_id = item_ids[0]
    second_item_id = item_ids[1]

    # Submit correct answer for the first item
    answer_params = ActivityAnswerCreate(
        activity_item_id=first_item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(
            activity_type=ActivityItemType.FREE_TEXT,
            text="Answer 1",
        ),
        is_correct=True,
        skip=False,
    )

    async with db_client.pool.connection() as conn:
        response = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            first_item_id,
            answer_params,
        )
        updated_item = await get_activity_item_in_transaction(
            conn,
            first_item_id,
            activity_id,
        )

    assert updated_item is not None
    assert updated_item.status == ActivityItemStatus.SUCCESS
    assert updated_item.attempted_retries == 1
    assert response.success_verdict is True
    assert response.hints == []
    assert response.next_item_id == str(second_item_id)
    assert response.activity_complete is False

    # Submit correct answer for the second item to complete activity
    answer_params_2 = ActivityAnswerCreate(
        activity_item_id=second_item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(
            activity_type=ActivityItemType.FREE_TEXT,
            text="Answer 2",
        ),
        is_correct=True,
        skip=False,
    )
    async with db_client.pool.connection() as conn:
        response_2 = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            second_item_id,
            answer_params_2,
        )
        updated_item_2 = await get_activity_item_in_transaction(
            conn,
            second_item_id,
            activity_id,
        )
    fetched_activity, _, _ = await queries.activity.get_activity_with_details_by_id(
        activity_id,
    )

    assert updated_item_2 is not None
    assert updated_item_2.status == ActivityItemStatus.SUCCESS
    assert updated_item_2.attempted_retries == 1
    assert response_2.success_verdict is True
    assert response_2.hints == []
    assert response_2.next_item_id is None
    assert response_2.activity_complete is True
    assert fetched_activity is not None
    assert fetched_activity.status == ActivityStatus.COMPLETED


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_incorrect_retries_remaining(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, _ = test_db_client_w_test_db
    user = create_user
    activity_id, item_ids = await _create_test_activity_and_items(
        db_client,
        user,
        max_retries_per_item=2,
    )
    item_id = item_ids[0]

    # Submit incorrect answer (1st attempt)
    answer_params = ActivityAnswerCreate(
        activity_item_id=item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(
            activity_type=ActivityItemType.FREE_TEXT,
            text="Wrong Answer",
        ),
        is_correct=False,
        skip=False,
    )

    async with db_client.pool.connection() as conn:
        response = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            item_id,
            answer_params,
        )
        updated_item = await get_activity_item_in_transaction(
            conn,
            item_id,
            activity_id,
        )

    assert updated_item is not None
    assert updated_item.status == ActivityItemStatus.NOT_TERMINATED
    assert updated_item.attempted_retries == 1
    assert response.success_verdict is False
    assert response.hints == [
        FreeTextAnswerHint(activity_type=ActivityItemType.FREE_TEXT),
    ]  # Updated hint assertion
    assert response.next_item_id is None
    assert response.activity_complete is False

    # Submit incorrect answer again (2nd attempt, still retries remaining)
    async with db_client.pool.connection() as conn:
        response_2 = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            item_id,
            answer_params,
        )
        updated_item_2 = await get_activity_item_in_transaction(
            conn,
            item_id,
            activity_id,
        )

    assert updated_item_2 is not None
    assert updated_item_2.status == ActivityItemStatus.RETRIES_EXHAUST
    assert updated_item_2.attempted_retries == 2
    assert response_2.success_verdict is False
    assert response_2.hints == [
        FreeTextAnswerHint(activity_type=ActivityItemType.FREE_TEXT),
    ]  # Updated hint assertion
    assert response_2.next_item_id is None
    assert response_2.activity_complete is True


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_incorrect_retries_exhausted(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, queries = test_db_client_w_test_db
    user = create_user
    activity_id, item_ids = await _create_test_activity_and_items(
        db_client,
        user,
        max_retries_per_item=1,
    )
    item_id = item_ids[0]

    # Submit incorrect answer (1st attempt, max_retries=1, so retries exhausted)
    answer_params = ActivityAnswerCreate(
        activity_item_id=item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(
            activity_type=ActivityItemType.FREE_TEXT,
            text="Wrong Answer",
        ),
        is_correct=False,
        skip=False,
    )

    async with db_client.pool.connection() as conn:
        response = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            item_id,
            answer_params,
        )
        updated_item = await get_activity_item_in_transaction(
            conn,
            item_id,
            activity_id,
        )
    fetched_activity, _, _ = await queries.activity.get_activity_with_details_by_id(
        activity_id,
    )

    assert updated_item is not None
    assert updated_item.status == ActivityItemStatus.RETRIES_EXHAUST
    assert updated_item.attempted_retries == 1
    assert response.success_verdict is False
    assert response.hints == [
        FreeTextAnswerHint(activity_type=ActivityItemType.FREE_TEXT),
    ]  # Updated hint assertion
    assert response.next_item_id is None
    assert response.activity_complete is True
    assert fetched_activity is not None
    assert fetched_activity.status == ActivityStatus.COMPLETED


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_skip(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, queries = test_db_client_w_test_db
    user = create_user
    activity_id, item_ids = await _create_test_activity_and_items(
        db_client,
        user,
        num_items=2,
    )
    first_item_id = item_ids[0]
    second_item_id = item_ids[1]

    # Submit skip for the first item
    answer_params = ActivityAnswerCreate(
        activity_item_id=first_item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(activity_type=ActivityItemType.FREE_TEXT, text=""),
        is_correct=False,
        skip=True,
    )

    async with db_client.pool.connection() as conn:
        response = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            first_item_id,
            answer_params,
        )
        updated_item = await get_activity_item_in_transaction(
            conn,
            first_item_id,
            activity_id,
        )

    assert updated_item is not None
    assert updated_item.status == ActivityItemStatus.SKIP
    assert updated_item.attempted_retries == 1  # Skip also increments attempts
    assert response.success_verdict is False
    assert response.hints == []
    assert response.next_item_id == str(second_item_id)
    assert response.activity_complete is False

    # Submit skip for the second item to complete activity
    answer_params_2 = ActivityAnswerCreate(
        activity_item_id=second_item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(activity_type=ActivityItemType.FREE_TEXT, text=""),
        is_correct=False,
        skip=True,
    )
    async with db_client.pool.connection() as conn:
        response_2 = await handle_submit_activity_item_answer(
            conn,
            activity_id,
            second_item_id,
            answer_params_2,
        )
        updated_item_2 = await get_activity_item_in_transaction(
            conn,
            second_item_id,
            activity_id,
        )
    fetched_activity, _, _ = await queries.activity.get_activity_with_details_by_id(
        activity_id,
    )

    assert updated_item_2 is not None
    assert updated_item_2.status == ActivityItemStatus.SKIP
    assert updated_item_2.attempted_retries == 1
    assert response_2.success_verdict is False
    assert response_2.hints == []
    assert response_2.next_item_id is None
    assert response_2.activity_complete is True
    assert fetched_activity is not None
    assert fetched_activity.status == ActivityStatus.COMPLETED


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_item_not_found(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, _ = test_db_client_w_test_db
    user = create_user
    activity_id, _ = await _create_test_activity_and_items(db_client, user)
    non_existent_item_id = uuid.uuid4()

    answer_params = ActivityAnswerCreate(
        activity_item_id=non_existent_item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(activity_type=ActivityItemType.FREE_TEXT, text="Answer"),
        is_correct=True,
        skip=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        async with db_client.pool.connection() as conn:
            await handle_submit_activity_item_answer(
                conn,
                activity_id,
                non_existent_item_id,
                answer_params,
            )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Activity item not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_item_wrong_activity(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, _ = test_db_client_w_test_db
    user = create_user
    activity_id_1, item_ids_1 = await _create_test_activity_and_items(db_client, user)
    activity_id_2, _ = await _create_test_activity_and_items(db_client, user)
    item_id_from_activity_1 = item_ids_1[0]

    answer_params = ActivityAnswerCreate(
        activity_item_id=item_id_from_activity_1,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(activity_type=ActivityItemType.FREE_TEXT, text="Answer"),
        is_correct=True,
        skip=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        async with db_client.pool.connection() as conn:
            # Try to submit item from activity_1 to activity_2
            await handle_submit_activity_item_answer(
                conn,
                activity_id_2,
                item_id_from_activity_1,
                answer_params,
            )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Activity item not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_submit_activity_item_answer_item_already_terminal(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, _ = test_db_client_w_test_db
    user = create_user
    activity_id, item_ids = await _create_test_activity_and_items(
        db_client,
        user,
        initial_item_status=ActivityItemStatus.SUCCESS,
    )
    item_id = item_ids[0]

    answer_params = ActivityAnswerCreate(
        activity_item_id=item_id,
        # activity_type=ActivityItemType.FREE_TEXT,
        answer=FreeTextAnswer(activity_type=ActivityItemType.FREE_TEXT, text="Answer"),
        is_correct=True,
        skip=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        async with db_client.pool.connection() as conn:
            await handle_submit_activity_item_answer(
                conn,
                activity_id,
                item_id,
                answer_params,
            )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Activity item is already in a terminal state." in exc_info.value.detail
