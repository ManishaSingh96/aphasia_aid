import uuid
from datetime import datetime, timezone

import pytest
from test_helpers.test_queries_model import TestQueries

from sia.db.connection import DatabaseClient
from sia.schemas.db.activity import Activity
from sia.schemas.db.activity_answer import ActivityAnswer
from sia.schemas.db.activity_item import ActivityItem
from sia.schemas.db.activity_types import (
    FreeTextAnswer,
    FreeTextQuestionConfig,
    FreeTextQuestionEvaluationConfig,
)
from sia.schemas.db.enums import ActivityItemType


@pytest.mark.asyncio
async def test_get_activity_by_id(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
) -> None:
    """Test retrieving an activity by its ID."""
    client, query = test_db_client_w_test_db
    activity_queries = query.activity

    # Create a dummy activity
    activity_id = uuid.uuid4()
    user_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    new_activity = Activity(id=activity_id, user_id=user_id, created_at=created_at)
    async with client.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO activity (id, user_id, created_at) VALUES (%s, %s, %s)",
                (new_activity.id, new_activity.user_id, new_activity.created_at),
            )
            await conn.commit()

    retrieved_activity = await activity_queries.get_activity_by_id(activity_id)
    assert retrieved_activity is not None
    assert retrieved_activity.id == activity_id
    assert retrieved_activity.user_id == user_id
    assert retrieved_activity.created_at == created_at

    # Test with a non-existent ID
    non_existent_activity = await activity_queries.get_activity_by_id(uuid.uuid4())
    assert non_existent_activity is None


@pytest.mark.asyncio
async def test_get_all_activities_of_user(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
) -> None:
    """Test retrieving all activities for a given user ID."""
    client, query = test_db_client_w_test_db
    activity_queries = query.activity

    user_id = uuid.uuid4()
    activity_id_1 = uuid.uuid4()
    activity_id_2 = uuid.uuid4()

    # Create dummy activities for the user
    created_at_1 = datetime.now(timezone.utc)
    created_at_2 = datetime.now(timezone.utc)
    activity_1 = Activity(id=activity_id_1, user_id=user_id, created_at=created_at_1)
    activity_2 = Activity(id=activity_id_2, user_id=user_id, created_at=created_at_2)

    async with client.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO activity (id, user_id, created_at) VALUES (%s, %s, %s)",
                (activity_1.id, activity_1.user_id, activity_1.created_at),
            )
            await cur.execute(
                "INSERT INTO activity (id, user_id, created_at) VALUES (%s, %s, %s)",
                (activity_2.id, activity_2.user_id, activity_2.created_at),
            )
            await conn.commit()

    activities = await activity_queries.get_all_activities_of_user(user_id)
    assert len(activities) == 2
    assert {a.id for a in activities} == {activity_id_1, activity_id_2}

    # Test with a non-existent user ID
    no_activities = await activity_queries.get_all_activities_of_user(uuid.uuid4())
    assert len(no_activities) == 0


@pytest.mark.asyncio
async def test_get_activity_item_by_id(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
) -> None:
    """Test retrieving an activity item by its ID and associated activity ID."""
    client, query = test_db_client_w_test_db
    activity_queries = query.activity

    activity_id = uuid.uuid4()
    user_id = uuid.uuid4()
    activity_item_id = uuid.uuid4()

    # Create dummy activity and activity item
    created_at = datetime.now(timezone.utc)
    activity = Activity(id=activity_id, user_id=user_id, created_at=created_at)
    activity_item = ActivityItem(
        id=activity_item_id,
        activity_id=activity_id,
        activity_type=ActivityItemType.FREE_TEXT,
        created_at=created_at,
        question_config=FreeTextQuestionConfig(
            activity_type="FREE_TEXT",
            prompt="Hello",
        ),
        question_evaluation_config=FreeTextQuestionEvaluationConfig(
            activity_type="FREE_TEXT",
            expected_answer="World",
        ),
    )

    async with client.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO activity (id, user_id, created_at) VALUES (%s, %s, %s)",
                (activity.id, activity.user_id, activity.created_at),
            )
            await cur.execute(
                """
                INSERT INTO activity_item (
                    id, activity_id, activity_type, created_at, question_config, question_evaluation_config
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    activity_item.id,
                    activity_item.activity_id,
                    activity_item.activity_type.value,
                    activity_item.created_at,
                    activity_item.question_config.model_dump_json(),
                    activity_item.question_evaluation_config.model_dump_json(),
                ),
            )
            await conn.commit()

    retrieved_item = await activity_queries.get_activity_item_by_id(
        activity_id,
        activity_item_id,
    )
    assert retrieved_item is not None
    assert retrieved_item.id == activity_item_id
    assert retrieved_item.activity_id == activity_id
    assert retrieved_item.question_config.prompt == "Hello"

    # Test with non-existent IDs
    non_existent_item = await activity_queries.get_activity_item_by_id(
        uuid.uuid4(),
        uuid.uuid4(),
    )
    assert non_existent_item is None


@pytest.mark.asyncio
async def test_get_activity_with_details_by_id(
    test_db_client_w_test_db: tuple[DatabaseClient, TestQueries],
) -> None:
    """Test retrieving an activity along with its items and answers."""
    client, query = test_db_client_w_test_db
    activity_queries = query.activity

    activity_id = uuid.uuid4()
    user_id = uuid.uuid4()
    item_id_1 = uuid.uuid4()
    item_id_2 = uuid.uuid4()
    answer_id_1 = uuid.uuid4()
    answer_id_2 = uuid.uuid4()

    # Create dummy activity, items, and answers
    created_at = datetime.now(timezone.utc)
    attempted_at = datetime.now(timezone.utc)
    activity = Activity(id=activity_id, user_id=user_id, created_at=created_at)
    item_1 = ActivityItem(
        id=item_id_1,
        activity_id=activity_id,
        activity_type=ActivityItemType.FREE_TEXT,
        created_at=created_at,
        question_config=FreeTextQuestionConfig(
            activity_type="FREE_TEXT",
            prompt="Item 1",
        ),
        question_evaluation_config=FreeTextQuestionEvaluationConfig(
            activity_type="FREE_TEXT",
            expected_answer="Answer 1",
        ),
    )
    item_2 = ActivityItem(
        id=item_id_2,
        activity_id=activity_id,
        activity_type=ActivityItemType.FREE_TEXT,
        created_at=created_at,
        question_config=FreeTextQuestionConfig(
            activity_type="FREE_TEXT",
            prompt="Item 2",
        ),
        question_evaluation_config=FreeTextQuestionEvaluationConfig(
            activity_type="FREE_TEXT",
            expected_answer="Answer 2",
        ),
    )
    answer_1 = ActivityAnswer(
        id=answer_id_1,
        activity_item_id=item_id_1,
        is_correct=True,
        answer=FreeTextAnswer(
            activity_type="FREE_TEXT",
            text="Answer 1",
        ),
        attempted_at=attempted_at,
    )
    answer_2 = ActivityAnswer(
        id=answer_id_2,
        activity_item_id=item_id_2,
        is_correct=False,
        answer=FreeTextAnswer(
            activity_type="FREE_TEXT",
            text="Wrong Answer",
        ),
        attempted_at=attempted_at,
    )

    async with client.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO activity (id, user_id, created_at) VALUES (%s, %s, %s)",
                (activity.id, activity.user_id, activity.created_at),
            )
            await cur.execute(
                """
                INSERT INTO activity_item (
                    id, activity_id, activity_type, created_at, question_config, question_evaluation_config
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    item_1.id,
                    item_1.activity_id,
                    item_1.activity_type.value,
                    item_1.created_at,
                    item_1.question_config.model_dump_json(),
                    item_1.question_evaluation_config.model_dump_json(),
                ),
            )
            await cur.execute(
                """
                INSERT INTO activity_item (
                    id, activity_id, activity_type, created_at, question_config, question_evaluation_config
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    item_2.id,
                    item_2.activity_id,
                    item_2.activity_type.value,
                    item_2.created_at,
                    item_2.question_config.model_dump_json(),
                    item_2.question_evaluation_config.model_dump_json(),
                ),
            )
            await cur.execute(
                """
                INSERT INTO activity_answer (
                    id, activity_item_id, is_correct, answer, attempted_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    answer_1.id,
                    answer_1.activity_item_id,
                    answer_1.is_correct,
                    answer_1.answer.model_dump_json(),
                    answer_1.attempted_at,
                ),
            )
            await cur.execute(
                """
                INSERT INTO activity_answer (
                    id, activity_item_id, is_correct, answer, attempted_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    answer_2.id,
                    answer_2.activity_item_id,
                    answer_2.is_correct,
                    answer_2.answer.model_dump_json(),
                    answer_2.attempted_at,
                ),
            )
            await conn.commit()

    (
        retrieved_activity,
        items,
        answers,
    ) = await activity_queries.get_activity_with_details_by_id(activity_id)

    assert retrieved_activity is not None
    assert retrieved_activity.id == activity_id
    assert len(items) == 2
    assert {i.id for i in items} == {item_id_1, item_id_2}
    assert len(answers) == 2
    assert {a.id for a in answers} == {answer_id_1, answer_id_2}
    assert items[0].question_config.prompt == "Item 1"
    assert items[1].question_config.prompt == "Item 2"
    assert answers[0].answer.text == "Answer 1"
    assert answers[1].answer.text == "Wrong Answer"

    (
        retrieved_activity,
        items,
        answers,
    ) = await activity_queries.get_activity_with_details_by_id(activity_id)

    assert retrieved_activity is not None
    assert retrieved_activity.id == activity_id
    assert len(items) == 2
    assert {i.id for i in items} == {item_id_1, item_id_2}
    assert len(answers) == 2
    assert {a.id for a in answers} == {answer_id_1, answer_id_2}

    # Test with non-existent activity ID
    (
        non_existent_activity,
        no_items,
        no_answers,
    ) = await activity_queries.get_activity_with_details_by_id(uuid.uuid4())
    assert non_existent_activity is None
    assert len(no_items) == 0
    assert len(no_answers) == 0


def test_sample_function(sample_fixture: str) -> None:
    """A sample test function that uses a fixture."""
    # S101: For simple equality checks, assert is idiomatic.
    # For more complex scenarios, pytest's assertion helpers might be preferred.
    assert sample_fixture == "sample_data"
