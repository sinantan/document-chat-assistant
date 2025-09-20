import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base
from app.models.mixins import DateMixin, DeleteMixin

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class Conversation(Base, DateMixin, DeleteMixin):
    __tablename__ = "conversations"
    
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    metadata_: Mapped[str] = mapped_column(
        "metadata",
        Text,
        nullable=True
    )
    
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
        lazy="select"
    )
    
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="select",
        order_by="Message.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"
