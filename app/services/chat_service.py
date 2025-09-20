import uuid
from typing import List, Optional, Tuple

import structlog

from app.clients.gemini_client import GeminiClient
from app.core.errors import NotFoundError, ValidationError
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base_repository import BaseRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatMessageRequest, ChatResponse, MessageRole
from app.services.document_service import DocumentService

logger = structlog.get_logger()


class ChatService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        document_service: DocumentService,
        gemini_client: GeminiClient
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.document_service = document_service
        self.gemini_client = gemini_client

    async def chat_with_document(
        self,
        user_id: uuid.UUID,
        chat_request: ChatMessageRequest
    ) -> ChatResponse:
        conversation = None
        
        if chat_request.conversation_id:
            conversation = await self._get_user_conversation(
                chat_request.conversation_id, user_id
            )
        elif chat_request.document_id:
            document = await self.document_service.get_document(
                chat_request.document_id, user_id
            )
            
            conversation = await self.conversation_repo.create_conversation(
                user_id=user_id,
                document_id=chat_request.document_id,
                title=self._generate_conversation_title(
                    document.original_filename, chat_request.message
                )
            )
        else:
            raise ValidationError("Either conversation_id or document_id is required")

        user_message = await self.message_repo.create_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=chat_request.message,
            token_count=self._estimate_tokens(chat_request.message)
        )

        try:
            conversation_history = await self._get_conversation_history(conversation.id)
            
            document_chunks = []
            if conversation.document_id:
                document_chunks = await self.document_service.get_document_chunks(
                    conversation.document_id, user_id
                )

            if document_chunks:
                ai_response = await self.gemini_client.chat_with_document(
                    message=chat_request.message,
                    document_chunks=document_chunks,
                    conversation_history=conversation_history
                )
            else:
                ai_response = await self.gemini_client.chat(
                    message=chat_request.message,
                    conversation_history=conversation_history
                )

            # Save assistant message
            assistant_message = await self.message_repo.create_message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=ai_response["content"],
                token_count=ai_response["usage"]["total_tokens"]
            )

            # Update conversation
            await self.conversation_repo.update_last_activity(conversation.id)

            logger.info(
                "Chat completed successfully",
                user_id=str(user_id),
                conversation_id=str(conversation.id),
                tokens_used=ai_response["usage"]["total_tokens"]
            )

            return ChatResponse(
                user_message=user_message,
                assistant_message=assistant_message,
                conversation=conversation,
                usage=ai_response["usage"]
            )

        except Exception as e:
            logger.error(
                "Chat failed",
                user_id=str(user_id),
                conversation_id=str(conversation.id) if conversation else None,
                error=str(e)
            )
            raise

    async def get_user_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        return await self.conversation_repo.get_user_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    async def get_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Message], Conversation]:
        # Verify user owns conversation
        conversation = await self._get_user_conversation(conversation_id, user_id)
        
        messages = await self.message_repo.get_conversation_messages(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
        
        return messages, conversation

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        # Verify user owns conversation
        conversation = await self._get_user_conversation(conversation_id, user_id)
        
        # Soft delete conversation and messages
        await self.conversation_repo.soft_delete(conversation_id)
        await self.message_repo.soft_delete_by_conversation(conversation_id)
        
        return True

    async def _get_user_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Conversation:
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise NotFoundError("Conversation not found")
        
        if conversation.user_id != user_id:
            raise NotFoundError("Conversation not found")
        
        if conversation.is_deleted:
            raise NotFoundError("Conversation not found")
        
        return conversation

    async def _get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 10
    ) -> List[dict]:
        messages = await self.message_repo.get_conversation_messages(
            conversation_id=conversation_id,
            skip=0,
            limit=limit
        )
        
        history = []
        for message in reversed(messages):
            history.append({
                "role": message.role,
                "content": message.content
            })
        
        return history

    def _generate_conversation_title(
        self,
        document_filename: str,
        first_message: str
    ) -> str:
        doc_name = document_filename.rsplit('.', 1)[0]  # Remove extension
        
        message_preview = first_message[:50]
        if len(first_message) > 50:
            message_preview += "..."
        
        return f"{doc_name}: {message_preview}"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
