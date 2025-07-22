from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.schemas import (
    DocumentCreate, 
    DocumentResponse, 
    AnalyzeDocumentRequest,
    AnalyzeDocumentResponse,
    DocumentAnalysisRequest
)
from app.services.document_analysis import DocumentAnalysisService
from app.models import Document, DocumentType, DocumentStatus
from app.database import get_db

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management"])
analysis_service = DocumentAnalysisService()


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Create a new document for analysis.
    """
    try:
        db_document = Document(
            title=document.title,
            content=document.content,
            originalFileName=document.originalFileName,
            mimeType=document.mimeType,
            type=document.type,
            status=DocumentStatus.PENDING,
            userId=user_id
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return DocumentResponse.model_validate(db_document)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/", response_model=List[DocumentResponse])
async def get_user_documents(
    user_id: UUID,
    document_type: DocumentType = None,
    status: DocumentStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all documents for a user with optional filtering.
    """
    try:
        query = db.query(Document).filter(Document.userId == user_id)
        
        if document_type:
            query = query.filter(Document.type == document_type)
        
        if status:
            query = query.filter(Document.status == status)
        
        documents = query.order_by(Document.createdAt.desc()).offset(skip).limit(limit).all()
        
        return [DocumentResponse.model_validate(doc) for doc in documents]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse.model_validate(document)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.post("/{document_id}/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    document_id: UUID,
    request: AnalyzeDocumentRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a legal document and extract key information including:
    - Summary
    - Hidden clauses
    - Risk assessment
    - Loopholes and red flags
    - Risk score and confidence rating
    - Key concerns
    
    Results are saved to database for future retrieval.
    """
    try:
        result = await analysis_service.analyze_document(document_id, request.user_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {str(e)}")


@router.get("/{document_id}/analysis", response_model=AnalyzeDocumentResponse)
async def get_document_analysis(
    document_id: UUID, 
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve analysis results for a document.
    """
    try:
        result = analysis_service.get_analysis_by_document_id(document_id, user_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all associated data.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully", "document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}") 