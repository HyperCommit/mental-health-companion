from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
def example_endpoint():
    return {"message": "Insights example endpoint"}