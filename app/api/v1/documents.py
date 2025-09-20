import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUser, get_document_service
from app.core.errors import DocumentChatException
from app.schemas.documents import (
    DocumentChunksResponse,
    DocumentListResponse, 
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

logger = structlog.get_logger()
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)




@router.post(
    "/",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        document = await document_service.upload_document(current_user.id, file, background_tasks)
        
        logger.info(
            "Document uploaded successfully",
            user_id=str(current_user.id),
            document_id=str(document.id),
            filename=document.original_filename,
            file_size=document.file_size,
        )
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_size=document.file_size,
            mime_type=document.mime_type,
            status=document.status,
        )
        
    except DocumentChatException:
        raise
    except Exception as e:
        logger.error(
            "Document upload failed",
            user_id=str(current_user.id),
            filename=file.filename,
            error=str(e),
        )
        raise


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="Get user's documents",
)
async def list_documents(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    document_service: DocumentService = Depends(get_document_service),
):
    documents = await document_service.get_user_documents(
        current_user.id, skip=skip, limit=limit
    )
    
    total = len(documents)
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    document_service: DocumentService = Depends(get_document_service),
):
    document = await document_service.get_document(document_id, current_user.id)
    return DocumentResponse.model_validate(document)


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunksResponse,
    summary="Get document text chunks",
)
async def get_document_chunks(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    document_service: DocumentService = Depends(get_document_service),
):
    chunks = await document_service.get_document_chunks(document_id, current_user.id)
    
    return DocumentChunksResponse(
        document_id=document_id,
        chunks=chunks,
        total_chunks=len(chunks),
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        await document_service.delete_document(document_id, current_user.id)
        
        logger.info(
            "Document deleted successfully",
            user_id=str(current_user.id),
            document_id=str(document_id),
        )
        
    except DocumentChatException:
        raise
    except Exception as e:
        logger.error(
            "Document deletion failed",
            user_id=str(current_user.id),
            document_id=str(document_id),
            error=str(e),
        )
        raise
