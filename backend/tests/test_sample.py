import uuid

import pytest
from test_helpers.test_queries_model import TestQueries

from sia.db.connection import DatabaseClient
from sia.db.transactions.activity_transactions import (
    CreateActivityParams,
    create_activity,
)
from sia.schemas.db.activity import ActivityCreate
from sia.schemas.db.activity_item import ActivityItemCreate
from sia.schemas.db.activity_types import (
    FreeTextQuestionConfig,
    FreeTextQuestionEvaluationConfig,
)
from sia.schemas.db.enums import ActivityItemStatus, ActivityItemType, ActivityStatus
from sia.schemas.db.user import User


@pytest.mark.asyncio
async def test_create_activity(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
    create_user: User,
) -> None:
    db_client, queries = test_db_client_w_test_db
    user = create_user

    # 2. Prepare activity item parameters
    question_config = FreeTextQuestionConfig(
        order=0,
        activity_type="FREE_TEXT",
        prompt="What is the capital of France?",
    )
    question_evaluation_config = FreeTextQuestionEvaluationConfig(
        activity_type="FREE_TEXT",
        expected_answer="Paris",
    )

    activity_item_create_params = [
        ActivityItemCreate(
            activity_id=uuid.uuid4(),  # Dummy activity_id
            max_retries=3,
            status=ActivityItemStatus.NOT_TERMINATED,
            activity_type=ActivityItemType.FREE_TEXT,
            question_config=question_config,
            question_evaluation_config=question_evaluation_config,
        ),
        ActivityItemCreate(
            activity_id=uuid.uuid4(),  # Dummy activity_id
            max_retries=1,
            status=ActivityItemStatus.NOT_TERMINATED,
            activity_type=ActivityItemType.FREE_TEXT,
            question_config=FreeTextQuestionConfig(
                order=1,
                activity_type="FREE_TEXT",
                prompt="What is 2+2?",
            ),
            question_evaluation_config=FreeTextQuestionEvaluationConfig(
                activity_type="FREE_TEXT",
                expected_answer="4",
            ),
        ),
    ]

    # 3. Prepare activity parameters
    activity_create_params = ActivityCreate(
        user_id=user.id,
        status=ActivityStatus.IDLE,
        generated_title="Test Activity Title",
    )

    create_activity_params = CreateActivityParams(
        activity_create_params=activity_create_params,
        activity_items_create_params=activity_item_create_params,
    )

    # 4. Call the create_activity transaction
    async with db_client.pool.connection() as conn:
        created_activity = await create_activity(conn, create_activity_params)

    # 5. Fetch the created activity and its items using queries
    (
        fetched_activity,
        fetched_items,
        _,
    ) = await queries.activity.get_activity_with_details_by_id(created_activity.id)

    # 6. Assertions
    assert fetched_activity is not None
    assert fetched_activity.id == created_activity.id
    assert fetched_activity.user_id == activity_create_params.user_id
    assert fetched_activity.status == activity_create_params.status
    assert fetched_activity.generated_title == activity_create_params.generated_title
    assert len(fetched_items) == len(activity_item_create_params)

    # Verify activity items
    for i, fetched_item in enumerate(fetched_items):
        expected_item = activity_item_create_params[i]
        assert fetched_item.activity_id == created_activity.id
        assert fetched_item.max_retries == expected_item.max_retries
        assert fetched_item.status == expected_item.status
        assert fetched_item.activity_type == expected_item.activity_type
        assert fetched_item.question_config == expected_item.question_config
        assert (
            fetched_item.question_evaluation_config
            == expected_item.question_evaluation_config
        )
