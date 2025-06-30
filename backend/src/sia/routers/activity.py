from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def test_activity() -> dict:
    return {"message": "Test activity router"}
