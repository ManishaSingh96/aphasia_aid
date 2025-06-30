from fastapi import Request

from sia.db.connection import DatabaseClient
from sia.db.queries.activity_queries import ActivityQueries


def get_db_client(request: Request) -> DatabaseClient:
    return request.app.state.dbClient


def get_activity_queries(request: Request) -> ActivityQueries:
    """Return the ActivityQueries instance from the application state."""
    return request.app.state.activityQueries
