from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pii_masking, document_analysis, chat, users
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="SignAware AI",
    description="AI-powered legal document analysis and PII masking service",
    version="1.0.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(document_analysis.router)
app.include_router(pii_masking.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to SignAware AI",
        "description": "AI-powered legal document analysis and PII masking service",
        "version": "1.0.0",
        "features": [
            "PII masking with Deepseek-R1:8B",
            "Legal document analysis with OpenAI GPT-4", 
            "Intelligent chat with document context",
            "Real-time streaming with SSE",
            "Persistent conversation history"
        ],
        "endpoints": {
            "users": {
                "create_user": "POST /api/v1/users/",
                "get_user": "GET /api/v1/users/{user_id}",
                "get_user_by_email": "GET /api/v1/users/email/{email}"
            },
            "documents": {
                "create_document": "POST /api/v1/documents/",
                "get_documents": "GET /api/v1/documents/",
                "get_document": "GET /api/v1/documents/{document_id}",
                "analyze_document": "POST /api/v1/documents/{document_id}/analyze",
                "get_analysis": "GET /api/v1/documents/{document_id}/analysis"
            },
            "pii_masking": {
                "mask_text": "POST /api/v1/pii/mask",
                "mask_document": "POST /api/v1/pii/mask/document/{document_id}",
                "get_masked_content": "GET /api/v1/pii/masked/{document_id}"
            },
            "chat": {
                "chat_streaming": "POST /api/v1/chat/stream",
                "chat_message": "POST /api/v1/chat/message",
                "chat_history": "GET /api/v1/chat/history/{session_id}",
                "chat_sessions": "GET /api/v1/chat/sessions/{document_id}"
            },
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "SignAware AI is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    ) 