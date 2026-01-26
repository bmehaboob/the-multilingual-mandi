"""Conversation management API endpoints"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.schemas.conversation import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    SendMessageRequest,
    MessageResponse,
    ConversationMessagesResponse,
    EndConversationResponse
)
from app.services.conversation_service import ConversationService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Initialize conversation service
conversation_service = ConversationService()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    
    Creates a new conversation with the specified participants. The current user
    must be included in the participant list. Users can have up to 5 concurrent
    active conversations.
    
    Requirements: 16.1, 16.2, 16.3
    
    Args:
        request: Conversation creation request
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ConversationResponse with conversation details
    
    Raises:
        HTTPException: If conversation limit reached or creation fails
    """
    logger.info(f"Creating conversation for user {current_user.id}")
    
    # Verify current user is in participant list
    if str(current_user.id) not in request.participant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user must be included in participant list"
        )
    
    # Check if user can create more conversations
    success, can_create, error = conversation_service.can_create_conversation(
        db, str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error
        )
    
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Create conversation
    success, conversation, error = conversation_service.create_conversation(
        db=db,
        participant_ids=request.participant_ids,
        commodity=request.commodity
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get message count (should be 0 for new conversation)
    message_count = 0
    
    logger.info(f"Created conversation {conversation.id}")
    
    return ConversationResponse(
        id=str(conversation.id),
        participants=[str(p) for p in conversation.participants],
        commodity=conversation.commodity,
        status=conversation.status.value,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=message_count,
        last_message_at=None
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    status_filter: Optional[str] = Query(None, description="Filter by status (active, completed, abandoned)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the current user.
    
    Returns all conversations where the current user is a participant,
    ordered by most recently updated. Optionally filter by status.
    
    Requirements: 16.1, 16.2
    
    Args:
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ConversationListResponse with list of conversations
    
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(f"Listing conversations for user {current_user.id}")
    
    # Get conversations
    success, conversations, error = conversation_service.get_user_conversations(
        db=db,
        user_id=str(current_user.id),
        status_filter=status_filter
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Build response with message counts
    conversation_responses = []
    active_count = 0
    
    for conv in conversations:
        # Count messages
        message_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conv.id
        ).scalar()
        
        # Get last message timestamp
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.timestamp.desc()).first()
        
        last_message_at = last_message.timestamp if last_message else None
        
        conversation_responses.append(ConversationResponse(
            id=str(conv.id),
            participants=[str(p) for p in conv.participants],
            commodity=conv.commodity,
            status=conv.status.value,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count,
            last_message_at=last_message_at
        ))
        
        if conv.status.value == 'active':
            active_count += 1
    
    logger.info(f"Retrieved {len(conversations)} conversations for user {current_user.id}")
    
    return ConversationListResponse(
        conversations=conversation_responses,
        total=len(conversations),
        active_count=active_count
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation.
    
    Returns details of a conversation. The current user must be a participant.
    
    Requirements: 16.2, 16.3
    
    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ConversationResponse with conversation details
    
    Raises:
        HTTPException: If conversation not found or user not authorized
    """
    logger.info(f"Getting conversation {conversation_id} for user {current_user.id}")
    
    # Get conversation
    success, conversation, error = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a participant" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    # Get message count and last message
    message_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id == conversation.id
    ).scalar()
    
    last_message = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp.desc()).first()
    
    last_message_at = last_message.timestamp if last_message else None
    
    return ConversationResponse(
        id=str(conversation.id),
        participants=[str(p) for p in conversation.participants],
        commodity=conversation.commodity,
        status=conversation.status.value,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=message_count,
        last_message_at=last_message_at
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a conversation.
    
    Updates conversation details such as commodity or status. The current user
    must be a participant.
    
    Requirements: 16.1, 16.5
    
    Args:
        conversation_id: Conversation ID
        request: Update request
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ConversationResponse with updated conversation details
    
    Raises:
        HTTPException: If conversation not found or update fails
    """
    logger.info(f"Updating conversation {conversation_id} for user {current_user.id}")
    
    # Update conversation
    success, conversation, error = conversation_service.update_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        commodity=request.commodity,
        status=request.status
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a participant" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    # Get message count and last message
    message_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id == conversation.id
    ).scalar()
    
    last_message = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp.desc()).first()
    
    last_message_at = last_message.timestamp if last_message else None
    
    return ConversationResponse(
        id=str(conversation.id),
        participants=[str(p) for p in conversation.participants],
        commodity=conversation.commodity,
        status=conversation.status.value,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=message_count,
        last_message_at=last_message_at
    )


@router.post("/{conversation_id}/end", response_model=EndConversationResponse)
async def end_conversation(
    conversation_id: str,
    final_status: str = Query("completed", description="Final status (completed or abandoned)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a conversation.
    
    Ends a conversation by setting its status to completed or abandoned.
    The current user must be a participant.
    
    Requirements: 16.5
    
    Args:
        conversation_id: Conversation ID
        final_status: Final status (completed or abandoned)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        EndConversationResponse confirming the operation
    
    Raises:
        HTTPException: If conversation not found or operation fails
    """
    logger.info(f"Ending conversation {conversation_id} for user {current_user.id}")
    
    # End conversation
    success, error = conversation_service.end_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        final_status=final_status
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a participant" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    return EndConversationResponse(
        success=True,
        message=f"Conversation ended with status: {final_status}",
        conversation_id=conversation_id,
        final_status=final_status
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a conversation.
    
    Sends a new message in the specified conversation. The current user must
    be a participant and the conversation must be active.
    
    Requirements: 16.3
    
    Args:
        conversation_id: Conversation ID
        request: Message request
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        MessageResponse with message details
    
    Raises:
        HTTPException: If conversation not found or message send fails
    """
    logger.info(f"Sending message in conversation {conversation_id} from user {current_user.id}")
    
    # Send message
    success, message, error = conversation_service.send_message(
        db=db,
        conversation_id=conversation_id,
        sender_id=str(current_user.id),
        original_text=request.original_text,
        original_language=request.original_language,
        translated_text=request.translated_text,
        audio_url=request.audio_url,
        message_metadata=request.message_metadata
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a participant" in error.lower() or "cannot send message" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    return MessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        sender_id=str(message.sender_id),
        original_text=message.original_text,
        original_language=message.original_language,
        translated_text=message.translated_text or {},
        audio_url=message.audio_url,
        timestamp=message.timestamp,
        message_metadata=message.message_metadata or {}
    )


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_messages(
    conversation_id: str,
    limit: Optional[int] = Query(None, description="Maximum number of messages to return", ge=1, le=100),
    offset: int = Query(0, description="Number of messages to skip", ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get messages from a conversation.
    
    Returns messages from the specified conversation with optional pagination.
    The current user must be a participant.
    
    Requirements: 16.3
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ConversationMessagesResponse with list of messages
    
    Raises:
        HTTPException: If conversation not found or user not authorized
    """
    logger.info(f"Getting messages from conversation {conversation_id} for user {current_user.id}")
    
    # Get messages
    success, messages, total_count, error = conversation_service.get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a participant" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    message_responses = [
        MessageResponse(
            id=str(msg.id),
            conversation_id=str(msg.conversation_id),
            sender_id=str(msg.sender_id),
            original_text=msg.original_text,
            original_language=msg.original_language,
            translated_text=msg.translated_text or {},
            audio_url=msg.audio_url,
            timestamp=msg.timestamp,
            message_metadata=msg.message_metadata or {}
        )
        for msg in messages
    ]
    
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=message_responses,
        total=total_count
    )


@router.get("/health")
async def conversation_health_check():
    """
    Health check endpoint for conversation service.
    
    Returns:
        Status information about the conversation service
    """
    return {
        "status": "healthy",
        "service": "conversations",
        "max_concurrent_conversations": ConversationService.MAX_CONCURRENT_CONVERSATIONS
    }
