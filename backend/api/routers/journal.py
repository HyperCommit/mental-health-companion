from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
def example_endpoint():
    return {"message": "Journal example endpoint"}