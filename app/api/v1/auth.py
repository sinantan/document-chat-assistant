import structlog
from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUser, get_auth_service
from app.schemas.auth import (
    AuthResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger()
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.register_user(user_data)
        logger.info("User registered successfully", email=user_data.email)
        return result
    except Exception as e:
        logger.error("User registration failed", email=user_data.email, error=str(e))
        raise


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user and get tokens",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.login_user(login_data)
        logger.info("User logged in successfully", email=login_data.email)
        return result
    except Exception as e:
        logger.error("User login failed", email=login_data.email, error=str(e))
        raise


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    refresh_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.refresh_token(refresh_data)
        logger.info("Token refreshed successfully")
        return result
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_user_profile(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_user_profile(current_user.id)
