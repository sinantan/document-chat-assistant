from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base
from app.models import Conversation
from app.models.mixins import DateMixin, DeleteMixin


class User(Base, DateMixin, DeleteMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
