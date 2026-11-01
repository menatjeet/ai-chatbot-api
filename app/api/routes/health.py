from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "AI Chatbot API is running",
        "status": "success"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }