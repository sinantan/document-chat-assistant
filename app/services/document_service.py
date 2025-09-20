import uuid
from typing import List, Optional

from fastapi import BackgroundTasks, UploadFile

from app.core.config import settings
from app.core.errors import FileProcessingError, NotFoundError, ValidationError
from app.models.document import Document, DocumentStatus
from app.repositories.base_repository import BaseRepository
from app.repositories.document_repository import DocumentRepository
from app.utils.pdf_processor import PDFProcessor


class DocumentService:
    def __init__(
        self, 
        document_repo: BaseRepository[Document],
        document_file_repo: DocumentRepository
    ):
        self.document_repo = document_repo
        self.file_repo = document_file_repo

    async def upload_document(
        self, 
        user_id: uuid.UUID, 
        file: UploadFile,
        background_tasks: BackgroundTasks
    ) -> Document:
        if not file.filename:
            raise ValidationError("Filename is required")
        
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise ValidationError(f"File type {file.content_type} not allowed")
        
        file_content = await file.read()
        
        if len(file_content) > settings.max_file_size_bytes:
            raise ValidationError(
                f"File size {len(file_content)} exceeds maximum {settings.max_file_size_bytes} bytes"
            )
        
        try:
            gridfs_file_id = await self.file_repo.store_file(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type,
                metadata={
                    "user_id": str(user_id),
                    "original_size": len(file_content)
                }
            )
            
            document = await self.document_repo.create({
                "user_id": user_id,
                "filename": self._generate_unique_filename(file.filename),
                "original_filename": file.filename,
                "file_size": len(file_content),
                "mime_type": file.content_type,
                "status": DocumentStatus.UPLOADING,
                "gridfs_file_id": gridfs_file_id
            })
            
            background_tasks.add_task(
                self._process_pdf_background,
                document.id,
                file_content
            )
            
            return document
            
        except Exception as e:
            raise FileProcessingError(f"Failed to upload document: {str(e)}")

    async def get_user_documents(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Document]:
        return await self.document_repo.get_all(
            skip=skip,
            limit=limit,
            filters={
                "user_id": user_id,
                "is_deleted": False
            }
        )

    async def get_document(
        self, 
        document_id: uuid.UUID, 
        user_id: Optional[uuid.UUID] = None
    ) -> Document:
        document = await self.document_repo.get_by_id(document_id)
        
        if not document:
            raise NotFoundError("Document not found")
        
        if user_id and document.user_id != user_id:
            raise NotFoundError("Document not found")
        
        if document.is_deleted:
            raise NotFoundError("Document not found")
        
        return document

    async def delete_document(
        self, 
        document_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> bool:
        document = await self.get_document(document_id, user_id)
        
        try:
            await self.file_repo.delete_file(document.gridfs_file_id)
            await self.file_repo.delete_document_chunks(str(document_id))
            
            await self.document_repo.soft_delete(document_id)
            
            return True
            
        except Exception as e:
            raise FileProcessingError(f"Failed to delete document: {str(e)}")

    async def get_document_content(
        self, 
        document_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> tuple[bytes, dict]:
        document = await self.get_document(document_id, user_id)
        
        try:
            content, metadata = await self.file_repo.get_file(document.gridfs_file_id)
            return content, metadata
            
        except Exception as e:
            raise FileProcessingError(f"Failed to get document content: {str(e)}")

    async def process_document_text(
        self, 
        document_id: uuid.UUID, 
        chunks: List[dict]
    ) -> bool:
        try:
            await self.file_repo.store_document_chunks(str(document_id), chunks)
            
            await self.document_repo.update(document_id, {
                "chunk_count": len(chunks),
                "status": DocumentStatus.COMPLETED
            })
            
            return True
            
        except Exception as e:
            await self._update_document_status(document_id, DocumentStatus.FAILED, str(e))
            raise FileProcessingError(f"Failed to process document text: {str(e)}")

    async def get_document_chunks(
        self, 
        document_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> List[dict]:
        await self.get_document(document_id, user_id)
        
        try:
            return await self.file_repo.get_document_chunks(str(document_id))
            
        except Exception as e:
            raise FileProcessingError(f"Failed to get document chunks: {str(e)}")

    async def _update_document_status(
        self, 
        document_id: uuid.UUID, 
        status: DocumentStatus, 
        error_message: Optional[str] = None
    ) -> None:
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message
        
        await self.document_repo.update(document_id, update_data)

    async def _process_pdf_background(self, document_id: uuid.UUID, file_content: bytes) -> None:
        try:
            await self._update_document_status(document_id, DocumentStatus.PROCESSING)
            
            pdf_data = PDFProcessor.process_pdf(file_content)
            
            await self.document_repo.update(document_id, {
                "page_count": pdf_data["page_count"],
                "chunk_count": pdf_data["chunk_count"]
            })
            
            await self.process_document_text(document_id, pdf_data["chunks"])
            
        except Exception as e:
            await self._update_document_status(document_id, DocumentStatus.FAILED, str(e))

    def _generate_unique_filename(self, original_filename: str) -> str:
        timestamp = uuid.uuid4().hex[:8]
        name_parts = original_filename.rsplit('.', 1)
        
        if len(name_parts) == 2:
            name, ext = name_parts
            return f"{name}_{timestamp}.{ext}"
        else:
            return f"{original_filename}_{timestamp}"
