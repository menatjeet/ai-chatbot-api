import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db, SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.message import (
    ChatResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.gemini import generate_ai_response, stream_ai_response

router = APIRouter(
    prefix="/api/conversations",
    tags=["Messages"]
)


# Create message and generate AI response
@router.post(
    "/{conversation_id}/messages",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED
)
def create_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check conversation ownership
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_data.content
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Generate AI response with conversation memory
    try:
        ai_text, interaction_id = generate_ai_response(
            prompt=message_data.content,
            previous_interaction_id=conversation.gemini_interaction_id
        )

        # Save latest Gemini interaction ID
        conversation.gemini_interaction_id = interaction_id
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="AI service is currently unavailable"
        )

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_text
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "user_message": user_message,
        "assistant_message": assistant_message
    }


# Stream AI response using Server-Sent Events (SSE)
@router.post(
    "/{conversation_id}/messages/stream",
    status_code=status.HTTP_200_OK
)
def create_message_stream(
    conversation_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check conversation ownership
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    previous_interaction_id = conversation.gemini_interaction_id
    user_msg_id = user_message.id
    user_msg_content = user_message.content

    def event_stream():
        # First send user message confirmation
        yield f"data: {json.dumps({'type': 'user_message', 'id': user_msg_id, 'content': user_msg_content})}\n\n"

        chunks = []
        last_interaction_id = None

        try:
            for kind, data in stream_ai_response(
                prompt=message_data.content,
                previous_interaction_id=previous_interaction_id
            ):
                if kind == "text":
                    chunks.append(data)
                    yield f"data: {json.dumps({'type': 'delta', 'content': data})}\n\n"
                elif kind == "completed":
                    last_interaction_id = data
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
            return

        final_ai_text = "".join(chunks)

        # Save assistant message in DB using the request db session
        try:
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_ai_text
            )
            db.add(assistant_message)
            if last_interaction_id:
                conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                if conv:
                    conv.gemini_interaction_id = last_interaction_id
            db.commit()
            db.refresh(assistant_message)
            yield f"data: {json.dumps({'type': 'done', 'assistant_message_id': assistant_message.id, 'interaction_id': last_interaction_id})}\n\n"
        except Exception:
            db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Failed to save assistant message'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Get conversation message history
@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse]
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check conversation ownership
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # Fetch messages in chronological order
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(
            Message.created_at.asc(),
            Message.id.asc()
        )
        .all()
    )

    return messages
