import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole:
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    document_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    token_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    document_id: Optional[uuid.UUID] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    skip: int
    limit: int


class ConversationMessagesResponse(BaseModel):
    conversation_id: uuid.UUID
    messages: List[ChatMessageResponse]
    total: int
    skip: int
    limit: int


class ChatResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    conversation: ConversationResponse
    usage: dict = {}


class ConversationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    document_id: Optional[uuid.UUID] = None
