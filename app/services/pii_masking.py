import httpx
import json
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Document

settings = get_settings()


class PIIMaskingService:
    def __init__(self):
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"
        self.model = settings.ollama_model

    async def mask_pii(self, text: str) -> str:
        """
        Mask PII information in the provided text using Ollama deepseek-r1 model.
        Skip the thinking step and return only the masked content.
        """
        prompt = f"""You are a PII (Personally Identifiable Information) masking expert. Your task is to identify and mask any PII in the provided text while preserving the document's meaning and structure.

PII to mask includes:
- Names (first, last, full names)
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- Addresses (street, city, state, zip)
- IP addresses
- Driver's license numbers
- Passport numbers
- Bank account numbers
- Date of birth
- Medical record numbers
- Employee IDs
- License plate numbers

Instructions:
1. Replace each PII item with a generic placeholder in brackets, like [NAME], [EMAIL], [PHONE], [ADDRESS], [SSN], etc.
2. Keep the same format and structure of the original text
3. Do not change any non-PII content
4. If no PII is found, return the original text unchanged
5. Respond ONLY with the masked text, no explanations, thinking process, or additional content
6. Do not include any reasoning or analysis - just provide the final masked text

Text to mask:
{text}

Masked text:"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            raw_response = result.get("response", "")
            
            # Skip thinking step if present (deepseek-r1 specific)
            if "<think>" in raw_response and "</think>" in raw_response:
                # Extract content after thinking block
                thinking_end = raw_response.find("</think>")
                if thinking_end != -1:
                    raw_response = raw_response[thinking_end + 8:].strip()
            
            # Clean up the response to get only the masked content
            lines = raw_response.split('\n')
            masked_content = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and explanatory text
                if line and not line.startswith(("Here", "The", "I've", "This")):
                    masked_content.append(line)
            
            return ' '.join(masked_content) if masked_content else raw_response.strip()

    async def mask_document_content(self, document_id: UUID, user_id: UUID, db: Session) -> dict:
        """
        Mask PII in a document's content and store the result.
        """
        # Get the document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found or access denied")

        try:
            # Mask the content
            masked_content = await self.mask_pii(document.content)
            
            # Prepare masked content data
            masked_data = {
                "original_content": document.content,
                "masked_content": masked_content,
                "original_length": len(document.content),
                "masked_length": len(masked_content),
                "masked_at": datetime.utcnow().isoformat(),
                "model_used": self.model
            }
            
            # Store in the maskedContent field
            document.maskedContent = masked_data
            db.commit()
            db.refresh(document)
            
            return {
                "document_id": document.id,
                "masked_content": masked_content,
                "original_length": len(document.content),
                "masked_length": len(masked_content),
                "masked_at": masked_data["masked_at"]
            }
            
        except Exception as e:
            raise Exception(f"Failed to mask document content: {str(e)}")

    async def get_masked_content(self, document_id: UUID, user_id: UUID, db: Session) -> dict:
        """
        Retrieve masked content for a document.
        """
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.userId == user_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found or access denied")
        
        if not document.maskedContent:
            raise ValueError("Document has not been processed for PII masking")
        
        return {
            "document_id": document.id,
            "masked_content": document.maskedContent.get("masked_content"),
            "original_length": document.maskedContent.get("original_length"),
            "masked_length": document.maskedContent.get("masked_length"),
            "masked_at": document.maskedContent.get("masked_at")
        } 