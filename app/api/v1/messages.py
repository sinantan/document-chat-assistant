import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUser, get_chat_service
from app.core.errors import DocumentChatException
from app.schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationMessagesResponse,
    ConversationResponse,
)
from app.services.chat_service import ChatService

logger = structlog.get_logger()
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a chat message",
)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    current_user: CurrentUser,
    chat_request: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        response = await chat_service.chat_with_document(current_user.id, chat_request)
        
        logger.info(
            "Chat message processed successfully",
            user_id=str(current_user.id),
            conversation_id=str(response.conversation.id),
            tokens_used=response.usage.get("total_tokens", 0),
        )
        
        return response
        
    except DocumentChatException:
        raise
    except Exception as e:
        logger.error(
            "Chat message processing failed",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="Get user's conversations",
)
async def list_conversations(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service),
):
    conversations = await chat_service.get_user_conversations(
        current_user.id, skip=skip, limit=limit
    )
    
    total = len(conversations)
    
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(conv) for conv in conversations],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
):
    conversations = await chat_service.get_user_conversations(current_user.id)
    
    for conv in conversations:
        if conv.id == conversation_id:
            return ConversationResponse.model_validate(conv)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Conversation not found"
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
    summary="Get conversation messages",
)
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service),
):
    messages, conversation = await chat_service.get_conversation_messages(
        conversation_id, current_user.id, skip=skip, limit=limit
    )
    
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=messages,
        total=len(messages),
        skip=skip,
        limit=limit,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        await chat_service.delete_conversation(conversation_id, current_user.id)
        
        logger.info(
            "Conversation deleted successfully",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
        )
        
    except DocumentChatException:
        raise
    except Exception as e:
        logger.error(
            "Conversation deletion failed",
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
            error=str(e),
        )
        raise
