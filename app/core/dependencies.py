from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthenticationError
from app.db.postgres import get_db
from app.models.document import Document
from app.models.user import User
from app.clients.gemini_client import GeminiClient
from app.repositories.base_repository import BaseRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService

security = HTTPBearer()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_conversation_repository(db: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db)


async def get_message_repository(db: AsyncSession = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)


async def get_document_repository() -> DocumentRepository:
    from app.db.mongo import mongodb
    
    if mongodb.client is None:
        from app.db.mongo import connect_to_mongo
        await connect_to_mongo()
    
    return DocumentRepository()


async def get_document_db_repository(db: AsyncSession = Depends(get_db)) -> BaseRepository[Document]:
    return BaseRepository(db, Document)


async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


async def get_gemini_client() -> GeminiClient:
    return GeminiClient()


async def get_document_service(
    doc_repo: BaseRepository[Document] = Depends(get_document_db_repository),
    doc_file_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    return DocumentService(doc_repo, doc_file_repo)


async def get_chat_service(
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    document_service: DocumentService = Depends(get_document_service),
    gemini_client: GeminiClient = Depends(get_gemini_client),
) -> ChatService:
    return ChatService(conversation_repo, message_repo, document_service, gemini_client)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
