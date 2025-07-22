import hashlib
from datetime import datetime
from uuid import UUID
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from app.config import get_settings
from app.models import Document, DocumentStatus
from app.schemas import DocumentAnalysisResult, AnalyzeDocumentResponse

settings = get_settings()


class AnalysisResult(BaseModel):
    """Structured output model for document analysis"""
    summary: str = Field(description="A comprehensive summary of the legal document")
    hidden_clauses: List[str] = Field(description="List of potentially hidden or obscure clauses")
    risk_assessment: str = Field(description="Overall risk assessment of the document")
    loopholes: List[str] = Field(description="Identified loopholes in the document")
    red_flags: List[str] = Field(description="Major red flags or concerning elements")
    risk_score: float = Field(description="Risk score out of 5 (1 = low risk, 5 = high risk)", ge=1, le=5)
    confidence_rating: float = Field(description="Confidence rating as percentage (0-100)", ge=0, le=100)
    key_concerns: List[str] = Field(description="Key concerns that users should be aware of")


class DocumentAnalysisService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3
        )
        self.output_parser = PydanticOutputParser(pydantic_object=AnalysisResult)

    async def analyze_document(self, document_id: UUID, user_id: UUID, db: Session) -> AnalyzeDocumentResponse:
        """
        Analyze a legal document and store results in the database.
        """
        # Get the document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found or access denied")
        
        # Check if already analyzed and completed
        if document.status == DocumentStatus.COMPLETED and document.analysis:
            analysis_result = DocumentAnalysisResult(**document.analysis)
            return AnalyzeDocumentResponse(
                document_id=document.id,
                status=document.status,
                analysis=analysis_result,
                processing_started_at=document.processingStartedAt,
                processing_completed_at=document.processingCompletedAt
            )

        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            document.processingStartedAt = datetime.utcnow()
            document.errorMessage = None
            db.commit()

            # Determine which content to use for analysis
            content_for_analysis = document.content  # Default to original content
            content_source = "original"
            content_description = "original unmasked content"
            content_note = ""
            
            # Check if masked content is available
            if document.maskedContent and document.maskedContent.get('masked_content'):
                content_for_analysis = document.maskedContent['masked_content']
                content_source = "masked"
                content_description = "PII has been masked for privacy"
                content_note = "Note: Personal identifiable information (PII) has been masked in this document for privacy protection."
                print(f"Using masked content for analysis of document {document_id}")
            else:
                print(f"No masked content available for document {document_id}, using original content")

            # Create prompt template
            prompt = PromptTemplate(
                template="""You are an expert legal analyst. Analyze the following legal document and provide a comprehensive analysis.

Document Title: {title}
Document Type: {doc_type}
Content Source: {content_source} content ({content_description})

Document Content:
{content}

Please analyze this document and provide:

1. A comprehensive summary of the document
2. Any hidden or obscure clauses that might not be immediately apparent
3. A risk assessment explaining potential risks to the user
4. Any loopholes you can identify
5. Red flags or concerning elements
6. A risk score out of 5 (1 = low risk, 5 = high risk)
7. Your confidence rating as a percentage (0-100)
8. Key concerns that users should be aware of

Be thorough and critical in your analysis. Focus on protecting the user's interests.
Consider the document type when analyzing - different types of documents have different risk patterns.
{content_note}

{format_instructions}
""",
                input_variables=["title", "doc_type", "content", "content_source", "content_description", "content_note"],
                partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
            )

            # Generate analysis
            chain = prompt | self.llm | self.output_parser
            result = await chain.ainvoke({
                "title": document.title,
                "doc_type": document.type.value,
                "content": content_for_analysis,
                "content_source": content_source,
                "content_description": content_description,
                "content_note": content_note
            })

            # Create analysis result with timestamp
            analysis_data = DocumentAnalysisResult(
                summary=result.summary,
                hidden_clauses=result.hidden_clauses,
                risk_assessment=result.risk_assessment,
                loopholes=result.loopholes,
                red_flags=result.red_flags,
                risk_score=result.risk_score,
                confidence_rating=result.confidence_rating,
                key_concerns=result.key_concerns,
                analyzed_at=datetime.utcnow()
            )

            # Update document with analysis results
            document.analysis = analysis_data.model_dump(mode='json')  # Use mode='json' to serialize datetime to ISO strings
            document.status = DocumentStatus.COMPLETED
            document.processingCompletedAt = datetime.utcnow()
            
            db.commit()
            db.refresh(document)

            return AnalyzeDocumentResponse(
                document_id=document.id,
                status=document.status,
                analysis=analysis_data,
                processing_started_at=document.processingStartedAt,
                processing_completed_at=document.processingCompletedAt
            )

        except Exception as e:
            # Update document with error status
            document.status = DocumentStatus.FAILED
            document.errorMessage = str(e)
            document.processingCompletedAt = datetime.utcnow()
            db.commit()
            
            return AnalyzeDocumentResponse(
                document_id=document.id,
                status=document.status,
                processing_started_at=document.processingStartedAt,
                processing_completed_at=document.processingCompletedAt,
                error_message=str(e)
            )

    def get_analysis_by_document_id(self, document_id: UUID, user_id: UUID, db: Session) -> AnalyzeDocumentResponse:
        """
        Retrieve analysis results for a document.
        """
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found or access denied")
        
        analysis_result = None
        if document.analysis:
            analysis_result = DocumentAnalysisResult(**document.analysis)
        
        return AnalyzeDocumentResponse(
            document_id=document.id,
            status=document.status,
            analysis=analysis_result,
            processing_started_at=document.processingStartedAt,
            processing_completed_at=document.processingCompletedAt,
            error_message=document.errorMessage
        ) 