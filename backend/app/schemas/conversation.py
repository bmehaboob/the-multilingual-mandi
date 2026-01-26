"""Conversation schemas for API requests and responses"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation"""
    participant_ids: List[str] = Field(
        ...,
        description="List of participant user IDs (including the creator)",
        min_items=2,
        max_items=10
    )
    commodity: Optional[str] = Field(
        None,
        description="Optional commodity being discussed",
        max_length=255
    )
    
    @validator('participant_ids')
    def validate_participants(cls, v):
        """Validate participant IDs"""
        if len(v) < 2:
            raise ValueError("At least 2 participants are required")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate participant IDs are not allowed")
        # Validate UUID format
        for participant_id in v:
            try:
                UUID(participant_id)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {participant_id}")
        return v


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation"""
    commodity: Optional[str] = Field(
        None,
        description="Update the commodity being discussed",
        max_length=255
    )
    status: Optional[str] = Field(
        None,
        description="Update conversation status (active, completed, abandoned)"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status value"""
        if v is not None:
            valid_statuses = ['active', 'completed', 'abandoned']
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class ConversationResponse(BaseModel):
    """Response containing conversation details"""
    id: str = Field(..., description="Conversation ID")
    participants: List[str] = Field(..., description="List of participant user IDs")
    commodity: Optional[str] = Field(None, description="Commodity being discussed")
    status: str = Field(..., description="Conversation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages in conversation")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response containing list of conversations"""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")
    active_count: int = Field(..., description="Number of active conversations")


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation"""
    original_text: str = Field(..., description="Original message text", min_length=1)
    original_language: str = Field(..., description="Language code (ISO 639-3)", max_length=10)
    translated_text: Optional[Dict[str, str]] = Field(
        None,
        description="Translations to other languages {language_code: translated_text}"
    )
    audio_url: Optional[str] = Field(None, description="URL to audio file", max_length=512)
    message_metadata: Optional[Dict] = Field(
        None,
        description="Metadata (transcription confidence, translation confidence, latency)"
    )
    
    @validator('original_language')
    def validate_language(cls, v):
        """Validate language code format"""
        if not v or len(v) < 2 or len(v) > 10:
            raise ValueError("Language code must be 2-10 characters")
        return v


class MessageResponse(BaseModel):
    """Response containing message details"""
    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    sender_id: str = Field(..., description="Sender user ID")
    original_text: str = Field(..., description="Original message text")
    original_language: str = Field(..., description="Language code")
    translated_text: Dict[str, str] = Field(default={}, description="Translations")
    audio_url: Optional[str] = Field(None, description="Audio URL")
    timestamp: datetime = Field(..., description="Message timestamp")
    message_metadata: Dict = Field(default={}, description="Message metadata")
    
    class Config:
        from_attributes = True


class ConversationMessagesResponse(BaseModel):
    """Response containing conversation messages"""
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")


class EndConversationResponse(BaseModel):
    """Response for ending a conversation"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    conversation_id: str = Field(..., description="Conversation ID")
    final_status: str = Field(..., description="Final conversation status")
