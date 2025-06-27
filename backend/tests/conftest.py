import pytest

# tests/
# ├── conftest.py               # db_session, http_client — global fixtures
# ├── test_helpers/             # shared test utilities and mock data (this will need a __init__.py)
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
