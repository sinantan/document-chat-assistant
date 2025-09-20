import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base
from app.models.mixins import DateMixin, DeleteMixin

if TYPE_CHECKING:
    from app.models.user import User


class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base, DateMixin, DeleteMixin):
    __tablename__ = "documents"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADING,
        nullable=False,
        index=True
    )
    
    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    
    gridfs_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    metadata_: Mapped[str] = mapped_column(
        "metadata",
        Text,
        nullable=True
    )
    
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
