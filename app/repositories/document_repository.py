import uuid
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.core.errors import FileProcessingError, NotFoundError
from app.db.mongo import get_gridfs_bucket, get_gridfs_sync, get_mongo_database
from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self):
        pass

    async def store_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        try:
            bucket = await get_gridfs_bucket()
            
            file_metadata = {
                "filename": filename,
                "contentType": content_type,
                "uploadDate": datetime.utcnow(),
                **(metadata or {})
            }
            
            file_id = await bucket.upload_from_stream(
                filename,
                BytesIO(file_content),
                metadata=file_metadata
            )
            
            return str(file_id)
            
        except Exception as e:
            raise FileProcessingError(f"Failed to store file: {str(e)}")

    async def get_file(self, file_id: str) -> tuple[bytes, dict]:
        try:
            bucket = await get_gridfs_bucket()
            
            grid_out = await bucket.open_download_stream(ObjectId(file_id))
            file_content = await grid_out.read()
            
            metadata = {
                "filename": grid_out.filename,
                "content_type": grid_out.metadata.get("contentType", "application/octet-stream"),
                "upload_date": grid_out.upload_date,
                "length": grid_out.length,
                **grid_out.metadata
            }
            
            return file_content, metadata
            
        except Exception as e:
            if "NoFile" in str(type(e)):
                raise NotFoundError(f"File with ID {file_id} not found")
            raise FileProcessingError(f"Failed to retrieve file: {str(e)}")

    async def delete_file(self, file_id: str) -> bool:
        try:
            bucket = await get_gridfs_bucket()
            await bucket.delete(ObjectId(file_id))
            return True
            
        except Exception as e:
            if "NoFile" in str(type(e)):
                return False
            raise FileProcessingError(f"Failed to delete file: {str(e)}")

    async def file_exists(self, file_id: str) -> bool:
        try:
            bucket = await get_gridfs_bucket()
            
            cursor = bucket.find({"_id": ObjectId(file_id)})
            files = await cursor.to_list(length=1)
            
            return len(files) > 0
            
        except Exception:
            return False

    async def get_file_metadata(self, file_id: str) -> dict:
        try:
            bucket = await get_gridfs_bucket()
            
            cursor = bucket.find({"_id": ObjectId(file_id)})
            files = await cursor.to_list(length=1)
            
            if not files:
                raise NotFoundError(f"File with ID {file_id} not found")
            
            file_doc = files[0]
            return {
                "file_id": str(file_doc._id),
                "filename": file_doc.filename,
                "content_type": file_doc.metadata.get("contentType", "application/octet-stream"),
                "upload_date": file_doc.uploadDate,
                "length": file_doc.length,
                **file_doc.metadata
            }
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            raise FileProcessingError(f"Failed to get file metadata: {str(e)}")

    async def store_document_chunks(
        self, 
        document_id: str, 
        chunks: List[dict]
    ) -> bool:
        try:
            database = await get_mongo_database()
            chunks_collection = database.chunks
            
            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk_doc = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {}),
                    "created_at": datetime.utcnow()
                }
                chunk_docs.append(chunk_doc)
            
            if chunk_docs:
                await chunks_collection.insert_many(chunk_docs)
            
            return True
            
        except Exception as e:
            raise FileProcessingError(f"Failed to store document chunks: {str(e)}")

    async def get_document_chunks(self, document_id: str) -> List[dict]:
        try:
            database = await get_mongo_database()
            chunks_collection = database.chunks
            
            cursor = chunks_collection.find(
                {"document_id": document_id}
            ).sort("chunk_index", 1)
            
            chunks = await cursor.to_list(length=None)
            
            return [
                {
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "metadata": chunk.get("metadata", {})
                }
                for chunk in chunks
            ]
            
        except Exception as e:
            raise FileProcessingError(f"Failed to retrieve document chunks: {str(e)}")

    async def delete_document_chunks(self, document_id: str) -> bool:
        try:
            database = await get_mongo_database()
            chunks_collection = database.chunks
            
            result = await chunks_collection.delete_many({"document_id": document_id})
            return result.deleted_count > 0
            
        except Exception as e:
            raise FileProcessingError(f"Failed to delete document chunks: {str(e)}")
