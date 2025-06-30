from fastapi import Request

from sia.db.queries.activity_queries import ActivityQueries


def get_activity_queries(request: Request) -> ActivityQueries:
    """Return the ActivityQueries instance from the application state."""
    return request.app.state.activityQueries
