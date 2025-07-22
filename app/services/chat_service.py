import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config import get_settings
from app.models import Document, ChatMessage, ChatMessageRole, DocumentStatus
from app.schemas import ChatMessageResponse

settings = get_settings()


class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
            streaming=True
        )

    def _get_document_context(self, document_id: UUID, user_id: UUID, db: Session) -> str:
        """Get document analysis context for the chat"""
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            return "No document found or access denied."
        
        if not document.analysis:
            return f"Document '{document.title}' has not been analyzed yet. Please analyze the document first to get detailed insights."

        analysis = document.analysis
        context = f"""
Document Information:
- Title: {document.title}
- Type: {document.type.value}
- Status: {document.status.value}

Document Analysis Summary:
- Summary: {analysis.get('summary', 'Not available')}
- Risk Score: {analysis.get('risk_score', 'Not available')}/5
- Confidence Rating: {analysis.get('confidence_rating', 'Not available')}%
- Risk Assessment: {analysis.get('risk_assessment', 'Not available')}

Hidden Clauses:
{chr(10).join(f'- {clause}' for clause in analysis.get('hidden_clauses', []))}

Loopholes:
{chr(10).join(f'- {loophole}' for loophole in analysis.get('loopholes', []))}

Red Flags:
{chr(10).join(f'- {flag}' for flag in analysis.get('red_flags', []))}

Key Concerns:
{chr(10).join(f'- {concern}' for concern in analysis.get('key_concerns', []))}

Analysis Date: {analysis.get('analyzed_at', 'Unknown')}
"""
        return context

    def _save_message(self, content: str, role: ChatMessageRole, session_id: str, 
                     document_id: UUID, user_id: UUID, db: Session) -> ChatMessage:
        """Save a chat message to the database"""
        message = ChatMessage(
            content=content,
            role=role,
            sessionId=session_id,
            documentId=document_id,
            userId=user_id,
            message_metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def _get_conversation_history(self, session_id: str, document_id: UUID, user_id: UUID, db: Session) -> List[Dict[str, str]]:
        """Get conversation history for context"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.sessionId == session_id,
            ChatMessage.documentId == document_id,
            ChatMessage.userId == user_id
        ).order_by(ChatMessage.createdAt).all()
        
        history = []
        for msg in messages:
            history.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        return history

    async def chat_stream(
        self, 
        message: str, 
        session_id: str, 
        document_id: UUID,
        user_id: UUID,
        db: Session
    ) -> AsyncGenerator[tuple[str, Optional[UUID]], None]:
        """
        Stream chat response using Server-Sent Events
        Returns tuples of (chunk, message_id) where message_id is only set for the final chunk
        """
        # Verify document access
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            yield ("Error: Document not found or access denied.", None)
            return
        
        # Save user message
        user_message = self._save_message(
            content=message,
            role=ChatMessageRole.USER,
            session_id=session_id,
            document_id=document_id,
            user_id=user_id,
            db=db
        )
        
        try:
            # Get document context and conversation history
            document_context = self._get_document_context(document_id, user_id, db)
            conversation_history = self._get_conversation_history(session_id, document_id, user_id, db)
            
            # Build messages for the LLM
            system_prompt = f"""You are a helpful AI assistant specialized in analyzing and discussing legal documents. 
You have access to the following document analysis:

{document_context}

Use this analysis to answer questions about the document. Be helpful, accurate, and always refer back to the specific 
analysis when relevant. If a user asks about something not covered in the analysis, politely explain that you can 
only discuss what's covered in the provided document analysis.

Always maintain a professional and helpful tone while being thorough in your responses."""

            # Prepare messages including conversation history
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history (excluding the current message we just saved)
            for hist_msg in conversation_history[:-1]:  # Exclude the last message (current user message)
                if hist_msg["role"] == "user":
                    messages.append(HumanMessage(content=hist_msg["content"]))
                elif hist_msg["role"] == "assistant":
                    messages.append(AIMessage(content=hist_msg["content"]))
            
            # Add current message
            messages.append(HumanMessage(content=message))

            # Stream response
            complete_response = ""
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    complete_response += chunk.content
                    yield (chunk.content, None)

            # Save assistant response
            if complete_response:
                assistant_message = self._save_message(
                    content=complete_response,
                    role=ChatMessageRole.ASSISTANT,
                    session_id=session_id,
                    document_id=document_id,
                    user_id=user_id,
                    db=db
                )
                # Yield final chunk with message ID
                yield ("", assistant_message.id)

        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            # Save error message
            assistant_message = self._save_message(
                content=error_message,
                role=ChatMessageRole.ASSISTANT,
                session_id=session_id,
                document_id=document_id,
                user_id=user_id,
                db=db
            )
            yield (error_message, assistant_message.id)

    async def get_chat_history(self, session_id: str, document_id: UUID, user_id: UUID, db: Session) -> List[ChatMessageResponse]:
        """Get chat history for a session and document"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.sessionId == session_id,
            ChatMessage.documentId == document_id,
            ChatMessage.userId == user_id
        ).order_by(ChatMessage.createdAt).all()
        
        return [
            ChatMessageResponse(
                id=msg.id,
                content=msg.content,
                role=msg.role,
                sessionId=msg.sessionId,
                message_metadata=msg.message_metadata,
                userId=msg.userId,
                documentId=msg.documentId,
                createdAt=msg.createdAt
            )
            for msg in messages
        ]

    def get_chat_sessions(self, document_id: UUID, user_id: UUID, db: Session) -> List[dict]:
        """Get all chat sessions for a document"""
        sessions = db.query(ChatMessage.sessionId).filter(
            ChatMessage.documentId == document_id,
            ChatMessage.userId == user_id,
            ChatMessage.sessionId.isnot(None)
        ).distinct().all()
        
        session_info = []
        for session in sessions:
            session_id = session[0]
            # Get first and last message for each session
            first_message = db.query(ChatMessage).filter(
                ChatMessage.sessionId == session_id,
                ChatMessage.documentId == document_id,
                ChatMessage.userId == user_id
            ).order_by(ChatMessage.createdAt).first()
            
            last_message = db.query(ChatMessage).filter(
                ChatMessage.sessionId == session_id,
                ChatMessage.documentId == document_id,
                ChatMessage.userId == user_id
            ).order_by(ChatMessage.createdAt.desc()).first()
            
            message_count = db.query(ChatMessage).filter(
                ChatMessage.sessionId == session_id,
                ChatMessage.documentId == document_id,
                ChatMessage.userId == user_id
            ).count()
            
            session_info.append({
                "session_id": session_id,
                "document_id": document_id,
                "first_message": first_message.content[:100] + "..." if first_message and len(first_message.content) > 100 else first_message.content if first_message else "",
                "message_count": message_count,
                "created_at": first_message.createdAt if first_message else None,
                "updated_at": last_message.createdAt if last_message else None
            })
        
        return sorted(session_info, key=lambda x: x["updated_at"] or x["created_at"], reverse=True) 