import os
import uuid
from typing import Awaitable, Callable, Tuple

from psycopg.sql import SQL
from psycopg.sql import Identifier as AsyncIdentifier
from psycopg_pool import AsyncConnectionPool

from sia.telemetry.log import get_logger

logger = get_logger(__name__)


# This function facilitates template-based testing for PostgreSQL databases.
# It creates a temporary, isolated database for each test run, ensuring tests are
# repeatable and don't interfere with each other.
#
# How it works:
# 1. Connects to the default 'postgres' database: This is necessary because
#    PostgreSQL does not allow creating or dropping databases while connected
#    to the database being operated on.
# 2. Generates a unique name for the temporary test database using `uuid.uuid4()`.
# 3. Kills existing connections to the `template_db_name`: PostgreSQL requires
#    no active connections to a template database when creating a new database
#    from it. This step ensures the `CREATE DATABASE ... TEMPLATE` operation succeeds.
# 4. Creates a new database from the `template_db_name`:
#    - The template database name is determined by the `TEST_TEMPLATE_DB` environment
#      variable (defaults to "template0"). This database must exist beforehand
#      and acts as a blueprint,
#      containing the schema (tables, indexes, etc.) and any baseline data
#      required for the tests. Any migrations that need to be applied should be
#      already applied to this template database.
#    - The owner of the new database is determined by the `TEST_TEMPLATE_DB_OWNER`
#      environment variable
#      (defaults to "postgres").
#    - The superuser connection string is determined by
#      `TEST_SUPER_USER_DATABASE_CONNECTION_STRING`
#      (defaults to "dbname=postgres user=postgres").
#    - This ensures each test starts with a consistent and known database state.
# 5. Returns the name of the temporary database and a `destroy_db` cleanup function.
#    The cleanup function is responsible for dropping the temporary database
#    after the test completes, preventing accumulation of test databases.
#
# NOTE: For supabase usage
# This would readily work when testing against a local postgres instance, all it
# needs is a test_db database created. That's the template DB otherwise you
# could just set it to whatever database has all your uptodate migrations.
#
# Supabase however has a distinct problem that the entire product is built
# around only the "postgres" user and database. So you cannot really CREATE
# DATABASE from the UI. But you can just use pgcli or direct postgres to create
# the database. After creating, just push your migrations to it and this should
# work as expected.
# NOTE: Another supabase problem
# Supabase is accessed behind an pooler, hence you cannot remove all connections
# so it'll not allow you to use it in the first place
async def create_test_db_async() -> Tuple[str, Callable[[], Awaitable[None]]]:
    """
    Create a temporary test database from a template.

    Returns its name and a cleanup function.
    """
    template_db_owner_role = os.getenv("TEST_TEMPLATE_DB_OWNER", "postgres")
    template_db_name = os.getenv("TEST_TEMPLATE_DB", "test_db")

    # This connection NEEDS superuser privileges to allow database
    # creation and termination.
    superuser_conn_string = os.getenv(
        "TEST_SUPER_USER_DATABASE_CONNECTION_STRING",
        "dbname=postgres user=postgres",  # Default for local PostgreSQL
    )
    pool = AsyncConnectionPool(
        min_size=1,
        max_size=1,
        conninfo=superuser_conn_string,
        open=False,
    )
    await pool.open()

    temp_db_name = f"test_{uuid.uuid4()}"

    kill_other_connections_sql = SQL(
        """
    SELECT
        pg_terminate_backend(pid)
    FROM
        pg_stat_activity
    WHERE
        pid <> pg_backend_pid() -- don't kill my own connection!
        AND datname = '{}';
    """,
    ).format(AsyncIdentifier(template_db_name))

    db_create_sql = SQL(
        """
    CREATE DATABASE {} WITH OWNER {} TEMPLATE {};
    """,
    ).format(
        AsyncIdentifier(temp_db_name),
        AsyncIdentifier(template_db_owner_role),
        AsyncIdentifier(template_db_name),
    )

    # create temp db
    async with pool.connection() as conn:
        await conn.set_autocommit(True)
        async with conn.cursor() as curs:
            await curs.execute(kill_other_connections_sql)
            await curs.execute(db_create_sql)

    # cleanup function
    async def destroy_db() -> None:
        sql = SQL("DROP DATABASE {} WITH (FORCE);").format(
            AsyncIdentifier(temp_db_name),
        )
        async with pool.connection() as conn:
            await conn.set_autocommit(True)
            async with conn.cursor() as curs:
                await curs.execute(sql)
        await pool.close()

    return temp_db_name, destroy_db
