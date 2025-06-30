from fastapi import Request

from sia.db.queries.car_queries import CarQueries


def get_car_queries(request: Request) -> CarQueries:
    """Return the CarQueries instance from the application state."""
    return request.app.state.carQueries
