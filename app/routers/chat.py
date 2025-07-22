import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from uuid import UUID
from typing import List
from app.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.chat_service import ChatService
from app.database import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])
chat_service = ChatService()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with the AI assistant using Server-Sent Events (SSE) for streaming responses.
    The bot uses document analysis as its source of truth and maintains conversation history
    in the database.
    """
    try:
        async def event_stream():
            message_id = None
            async for chunk, msg_id in chat_service.chat_stream(
                message=request.message,
                session_id=request.session_id,
                document_id=request.document_id,
                user_id=request.user_id,
                db=db
            ):
                if chunk:  # Only send non-empty chunks
                    # Format as SSE data
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": chunk, 
                            "session_id": request.session_id,
                            "document_id": str(request.document_id)
                        })
                    }
                
                if msg_id:  # Final message with ID
                    message_id = msg_id
            
            # Send end event with message ID
            yield {
                "event": "end",
                "data": json.dumps({
                    "session_id": request.session_id,
                    "document_id": str(request.document_id),
                    "message_id": str(message_id) if message_id else None
                })
            }

        return EventSourceResponse(event_stream())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat stream failed: {str(e)}")


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Non-streaming chat endpoint that returns the complete response.
    """
    try:
        complete_response = ""
        message_id = None
        
        async for chunk, msg_id in chat_service.chat_stream(
            message=request.message,
            session_id=request.session_id,
            document_id=request.document_id,
            user_id=request.user_id,
            db=db
        ):
            if chunk:
                complete_response += chunk
            if msg_id:
                message_id = msg_id
        
        return ChatResponse(
            response=complete_response,
            session_id=request.session_id,
            message_id=message_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve the chat history for a specific session and document.
    """
    try:
        messages = await chat_service.get_chat_history(session_id, document_id, user_id, db)
        return ChatHistoryResponse(
            session_id=session_id,
            document_id=document_id,
            messages=messages,
            total_messages=len(messages)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.get("/sessions/{document_id}")
async def get_chat_sessions(
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for a document.
    """
    try:
        sessions = chat_service.get_chat_sessions(document_id, user_id, db)
        return {
            "document_id": document_id,
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat sessions: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete all messages in a chat session.
    """
    try:
        from app.models import ChatMessage
        
        # Delete all messages in the session
        deleted_count = db.query(ChatMessage).filter(
            ChatMessage.sessionId == session_id,
            ChatMessage.documentId == document_id,
            ChatMessage.userId == user_id
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Deleted {deleted_count} messages from session",
            "session_id": session_id,
            "document_id": document_id,
            "deleted_messages": deleted_count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}") 