from typing import AsyncGenerator

import pytest
from test_helpers.realmock_db import create_test_db_async
from test_helpers.test_queries_model import TestQueries

from sia.db.connection import DatabaseClient
from sia.db.queries.activity_queries import ActivityQueries

# tests/
# ├── conftest.py               # db_session, http_client — global fixtures
# ├── test_helpers/             # shared test utilities and mock data
# │   └── __init__.py
# ├── test_data/                # mock data etc.
# ├── package_a/
# │   ├── test_xyz.py
# │   ├── conftest.py           # fixtures (package_a)
# │   ├── test_helpers/         # shared test utilities and mock data (package_a)
# │   └── test_data/            # mock data etc. (package_a)
# ├── package_b/
# │   ├── test_pqr.py
# │   ├── conftest.py           # fixtures (package_b)
# │   ├── test_helpers/         # shared test utilities and mock data (package b)
# │   └── test_data/            # mock data etc. (package_b)


@pytest.fixture
def sample_fixture() -> str:
    """Provide sample sia data for tests."""
    return "sample_data"


@pytest.fixture
async def test_db_client_w_test_db() -> AsyncGenerator[
    tuple[DatabaseClient, TestQueries],
    None,
]:
    """Provide a test database client with a seeded database."""
    db_name, destroy_db = await create_test_db_async()
    client = await DatabaseClient.create(
        min_size=1,
        max_size=5,
        conn_str=f"dbname={db_name}",
    )
    queries = TestQueries(
        activity=ActivityQueries(client),
    )
    await client.seed()
    yield client, queries
    await client.close()
    await destroy_db()
