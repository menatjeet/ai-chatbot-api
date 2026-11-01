from fastapi import APIRouter , Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db


router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "AI Chatbot API is running",
        "status": "success",
        "docs_url": "/docs",
        "chat_ui": "/chat"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }



@router.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "status": "success"
    }