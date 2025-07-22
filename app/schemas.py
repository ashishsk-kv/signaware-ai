from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models import UserRole, DocumentType, DocumentStatus, ChatMessageRole


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER


class UserCreate(UserBase):
    password: Optional[str] = None
    googleId: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    isEmailVerified: bool
    isActive: bool
    avatar: Optional[str] = None
    lastLoginAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# PII Masking schemas
class PIIMaskingRequest(BaseModel):
    text: str
    userId: UUID


class PIIMaskingResponse(BaseModel):
    masked_content: str
    original_length: int
    masked_length: int


# Document schemas
class DocumentCreate(BaseModel):
    title: str
    content: str
    type: DocumentType = DocumentType.OTHER
    originalFileName: Optional[str] = None
    mimeType: Optional[str] = None

    @field_validator('type', mode='before')
    @classmethod
    def convert_document_type(cls, v):
        """Convert case-insensitive string to proper DocumentType enum"""
        if isinstance(v, str):
            # Handle case-insensitive conversion
            v_lower = v.lower()
            for doc_type in DocumentType:
                if doc_type.value == v_lower:
                    return doc_type
            # If not found by value, try by name (for backward compatibility)
            v_upper = v.upper()
            for doc_type in DocumentType:
                if doc_type.name == v_upper:
                    return doc_type
            # If still not found, let Pydantic handle the validation error
        return v


class DocumentAnalysisResult(BaseModel):
    """Analysis results structure stored in the analysis JSONB field"""
    summary: str
    hidden_clauses: List[str]
    risk_assessment: str
    loopholes: List[str]
    red_flags: List[str]
    risk_score: float = Field(..., ge=1, le=5)
    confidence_rating: float = Field(..., ge=0, le=100)
    key_concerns: List[str]
    analyzed_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    content: str
    originalFileName: Optional[str] = None
    type: DocumentType
    status: DocumentStatus
    analysis: Optional[DocumentAnalysisResult] = None
    processingStartedAt: Optional[datetime] = None
    processingCompletedAt: Optional[datetime] = None
    errorMessage: Optional[str] = None
    userId: UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class DocumentAnalysisRequest(BaseModel):
    document_id: UUID
    userId: UUID


# Chat schemas
class ChatMessageCreate(BaseModel):
    content: str
    role: ChatMessageRole = ChatMessageRole.USER
    sessionId: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    id: UUID
    content: str
    role: ChatMessageRole
    sessionId: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    userId: UUID
    documentId: UUID
    createdAt: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: str
    document_id: UUID
    user_id: UUID


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: UUID


class ChatHistoryResponse(BaseModel):
    session_id: str
    document_id: UUID
    messages: List[ChatMessageResponse]
    total_messages: int


# Analysis request for existing documents
class AnalyzeDocumentRequest(BaseModel):
    user_id: UUID


# Response for document analysis
class AnalyzeDocumentResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    analysis: Optional[DocumentAnalysisResult] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None 