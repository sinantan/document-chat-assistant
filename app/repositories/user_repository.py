import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.is_active == True,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(
                User.email == email,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_user(
        self, 
        email: str, 
        hashed_password: str, 
        full_name: Optional[str] = None
    ) -> User:
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
        }
        return await self.create(user_data)

    async def update_password(self, user_id: uuid.UUID, hashed_password: str) -> Optional[User]:
        return await self.update(user_id, {"hashed_password": hashed_password})

    async def deactivate_user(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.update(user_id, {"is_active": False})

    async def activate_user(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.update(user_id, {"is_active": True})
