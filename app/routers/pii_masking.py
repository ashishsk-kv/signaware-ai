from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.schemas import PIIMaskingRequest, PIIMaskingResponse
from app.services.pii_masking import PIIMaskingService
from app.database import get_db

router = APIRouter(prefix="/api/v1/pii", tags=["PII Masking"])
pii_service = PIIMaskingService()


@router.post("/mask", response_model=PIIMaskingResponse)
async def mask_pii_text(request: PIIMaskingRequest, db: Session = Depends(get_db)):
    """
    Mask personally identifiable information (PII) in the provided text.
    Uses locally running Deepseek-R1:8B model on Ollama.
    """
    try:
        masked_content = await pii_service.mask_pii(request.text)
        return PIIMaskingResponse(
            masked_content=masked_content,
            original_length=len(request.text),
            masked_length=len(masked_content)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mask PII: {str(e)}")


@router.post("/mask/document/{document_id}")
async def mask_document_pii(
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Mask PII in a document's content and store the result in the database.
    """
    try:
        result = await pii_service.mask_document_content(document_id, user_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mask document PII: {str(e)}")


@router.get("/masked/{document_id}")
async def get_masked_document_content(
    document_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve masked content for a document.
    """
    try:
        result = await pii_service.get_masked_content(document_id, user_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve masked content: {str(e)}") 