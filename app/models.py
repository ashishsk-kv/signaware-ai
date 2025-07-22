from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Enum, ForeignKey, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    LEGAL_ADVISOR = "legal_advisor"
    CUSTOMER = "customer"
    ADMIN = "admin"


class DocumentType(str, enum.Enum):
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Custom enum type decorator that forces using enum values
class EnumAsString(TypeDecorator):
    """A custom type that stores enum values as strings."""
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to string value for database storage"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value  # Use the enum value, not the name
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert string value back to enum when reading from database"""
        if value is None:
            return None
        # Find enum by value
        for enum_item in self.enum_class:
            if enum_item.value == value:
                return enum_item
        # If not found, return the raw value
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email = Column(String, nullable=False, unique=True)
    password = Column('password', String, nullable=True)
    firstName = Column('firstName', String, nullable=True)
    lastName = Column('lastName', String, nullable=True)
    role = Column('role', EnumAsString(UserRole), nullable=False, default=UserRole.CUSTOMER)
    googleId = Column('googleId', String, nullable=True)
    avatar = Column(String, nullable=True)
    isEmailVerified = Column('isEmailVerified', Boolean, nullable=False, default=False)
    emailVerificationToken = Column('emailVerificationToken', String, nullable=True)
    passwordResetToken = Column('passwordResetToken', String, nullable=True)
    passwordResetExpires = Column('passwordResetExpires', DateTime, nullable=True)
    isActive = Column('isActive', Boolean, nullable=False, default=True)
    lastLoginAt = Column('lastLoginAt', DateTime, nullable=True)
    createdAt = Column('createdAt', DateTime(timezone=True), nullable=False, server_default=func.now())
    updatedAt = Column('updatedAt', DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    title = Column(String, nullable=False)
    content = Column('content', Text, nullable=False)
    originalFileName = Column('originalFileName', String, nullable=True)
    filePath = Column('filePath', String, nullable=True)
    fileSize = Column('fileSize', Integer, nullable=True)
    mimeType = Column('mimeType', String, nullable=True)
    type = Column('type', EnumAsString(DocumentType), nullable=False, default=DocumentType.OTHER)
    status = Column(EnumAsString(DocumentStatus), nullable=False, default=DocumentStatus.PENDING)
    analysis = Column(JSONB, nullable=True)  # Store analysis results here
    maskedContent = Column('maskedContent', JSONB, nullable=True)  # Store masked content here
    processingStartedAt = Column('processingStartedAt', DateTime, nullable=True)
    processingCompletedAt = Column('processingCompletedAt', DateTime, nullable=True)
    errorMessage = Column('errorMessage', String, nullable=True)
    userId = Column('userId', UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column('createdAt', DateTime(timezone=True), nullable=False, server_default=func.now())
    updatedAt = Column('updatedAt', DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    content = Column('content', Text, nullable=False)
    role = Column('role', EnumAsString(ChatMessageRole), nullable=False, default=ChatMessageRole.USER)
    sessionId = Column('sessionId', String, nullable=True)
    message_metadata = Column('metadata', JSONB, nullable=True)  # Maps to 'metadata' column in database
    userId = Column('userId', UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    documentId = Column('documentId', UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column('createdAt', DateTime(timezone=True), nullable=False, server_default=func.now())
    updatedAt = Column('updatedAt', DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_messages")
    document = relationship("Document", back_populates="chat_messages") 