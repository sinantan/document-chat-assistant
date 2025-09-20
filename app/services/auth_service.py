import uuid
from typing import Optional

from app.core.config import settings
from app.core.errors import AuthenticationError, ValidationError
from app.core.security import SecurityManager
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
        self.security = SecurityManager()

    async def register_user(self, user_data: UserRegisterRequest) -> AuthResponse:
        if await self.user_repo.email_exists(user_data.email):
            raise ValidationError("User with this email already exists")

        hashed_password = self.security.hash_password(user_data.password)
        
        user = await self.user_repo.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        return await self._create_auth_response(user)

    async def login_user(self, login_data: UserLoginRequest) -> AuthResponse:
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        if not self.security.verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        return await self._create_auth_response(user)

    async def refresh_token(self, refresh_data: TokenRefreshRequest) -> TokenResponse:
        if not self.security.validate_token_type(refresh_data.refresh_token, "refresh"):
            raise AuthenticationError("Invalid refresh token type")

        user_id = self.security.get_user_id_from_token(refresh_data.refresh_token)
        user = await self.user_repo.get_active_by_id(user_id)
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        access_token = self.security.create_access_token(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_current_user(self, token: str) -> User:
        if not self.security.validate_token_type(token, "access"):
            raise AuthenticationError("Invalid access token type")

        user_id = self.security.get_user_id_from_token(token)
        user = await self.user_repo.get_active_by_id(user_id)
        
        if not user:
            raise AuthenticationError("User not found or inactive")

        return user

    async def get_user_profile(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    async def _create_auth_response(self, user: User) -> AuthResponse:
        access_token = self.security.create_access_token(str(user.id))
        refresh_token = self.security.create_refresh_token(str(user.id))

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

        return AuthResponse(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
