from fastapi import APIRouter, Depends

from sia.db.queries.car_queries import CarQueries
from sia.routers.dependencies.db import get_car_queries

router = APIRouter()

# Define a module-level variable for the dependency
car_queries_dependency = Depends(get_car_queries)


@router.get("/cars/count", response_model=int)
async def get_cars_count(queries: CarQueries = car_queries_dependency) -> int:
    """Get the total count of cars."""
    count: int = await queries.get_all_cars_count()
    return count


# Add more car-related endpoints here
