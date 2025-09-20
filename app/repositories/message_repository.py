import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Message)

    async def get_by_conversation_id(
        self, 
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False
            )
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50
    ) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))

    async def get_last_messages(
        self,
        conversation_id: uuid.UUID,
        count: int = 10
    ) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False
            )
            .order_by(Message.created_at.desc())
            .limit(count)
        )
        messages = result.scalars().all()
        return list(reversed(messages))

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        token_count: Optional[int] = None,
        metadata: Optional[str] = None
    ) -> Message:
        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "token_count": token_count,
            "metadata_": metadata,
        }
        return await self.create(message_data)

    async def get_user_messages(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole = MessageRole.USER
    ) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == role,
                Message.is_deleted == False
            )
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()

    async def count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        return await self.count({
            "conversation_id": conversation_id,
            "is_deleted": False
        })

    async def get_conversation_messages(
        self, 
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        return await self.get_by_conversation_id(conversation_id, skip, limit)

    async def soft_delete_by_conversation(self, conversation_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        )
        messages = result.scalars().all()
        
        for message in messages:
            await self.soft_delete(message.id)
        
        return True

    async def get_total_tokens_by_conversation(self, conversation_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(Message.token_count)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False,
                Message.token_count.isnot(None)
            )
        )
        token_counts = result.scalars().all()
        return sum(count for count in token_counts if count is not None)
