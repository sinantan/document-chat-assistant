import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Conversation)

    async def get_by_user_id(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False
            )
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_user_conversations(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Conversation]:
        return await self.get_by_user_id(user_id, skip, limit)

    async def get_by_document_id(
        self, 
        document_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> List[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.document_id == document_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted == False
            )
            .order_by(Conversation.created_at.desc())
        )
        return result.scalars().all()

    async def get_with_messages(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_id(
        self, 
        conversation_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        title: Optional[str] = None,
        metadata: Optional[str] = None
    ) -> Conversation:
        conversation_data = {
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "metadata_": metadata,
        }
        return await self.create(conversation_data)

    async def update_title(
        self, 
        conversation_id: uuid.UUID, 
        title: str
    ) -> Optional[Conversation]:
        return await self.update(conversation_id, {"title": title})

    async def update_last_activity(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        from datetime import datetime
        return await self.update(conversation_id, {"updated_at": datetime.utcnow()})

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        return await self.count({
            "user_id": user_id,
            "is_deleted": False
        })
