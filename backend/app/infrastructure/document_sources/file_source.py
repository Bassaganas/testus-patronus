from typing import Dict, Any
from fastapi import UploadFile
from app.infrastructure.document_sources.base import DocumentSource, DocumentData
from app.core.exceptions import ValidationException
import aiofiles
import os
import magic
import logging
import tempfile
from pypdf import PdfReader
import io

logger = logging.getLogger(__name__)

class FileDocumentSource(DocumentSource):
    """Document source for file uploads."""
    
    SUPPORTED_MIME_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'text/markdown': '.md',
        'text/html': '.html',
        'text/csv': '.csv',
        'application/json': '.json'
    }
    
    async def process_upload(self, file: UploadFile) -> DocumentData:
        """Process an uploaded file."""
        try:
            # Validate file type
            content_type = file.content_type
            if content_type not in self.SUPPORTED_MIME_TYPES:
                raise ValidationException(f"Unsupported file type: {content_type}")
            
            # Read file content
            content = await file.read()
            
            # Detect actual file type
            mime = magic.Magic(mime=True)
            detected_type = mime.from_buffer(content)
            
            if detected_type not in self.SUPPORTED_MIME_TYPES:
                raise ValidationException(f"Unsupported file type: {detected_type}")
            
            # Process content based on file type
            text_content = await self._extract_text(content, detected_type)
            
            return DocumentData(
                title=file.filename,
                content=text_content,
                metadata={
                    "original_filename": file.filename,
                    "content_type": detected_type,
                    "file_size": len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise ValidationException(f"Error processing file: {str(e)}")
    
    async def process_document(self, source_id: str) -> DocumentData:
        """This method is not applicable for file uploads."""
        raise ValidationException("File source does not support direct document processing")
    
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """No credentials needed for file uploads."""
        return True
    
    async def _extract_text(self, content: bytes, content_type: str) -> str:
        """Extract text content from different file types."""
        if content_type == 'text/plain':
            return content.decode('utf-8')
        elif content_type == 'application/pdf':
            # Extract text from PDF
            try:
                # Create a BytesIO object from the content
                pdf_file = io.BytesIO(content)
                
                # Create a PDF reader object
                pdf_reader = PdfReader(pdf_file)
                
                # Extract text from all pages
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                return text
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {str(e)}")
                raise ValidationException(f"Error extracting text from PDF: {str(e)}")
        elif content_type == 'text/markdown':
            # For markdown, just return the raw content
            return content.decode('utf-8')
        elif content_type == 'text/html':
            # For HTML, just return the raw content
            return content.decode('utf-8')
        elif content_type == 'text/csv':
            # For CSV, just return the raw content
            return content.decode('utf-8')
        elif content_type == 'application/json':
            # For JSON, just return the raw content
            return content.decode('utf-8')
        else:
            raise ValidationException(f"Text extraction not implemented for {content_type}") 