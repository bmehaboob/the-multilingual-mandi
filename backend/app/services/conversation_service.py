"""Conversation management service"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.conversation import Conversation, Message, ConversationStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages"""
    
    MAX_CONCURRENT_CONVERSATIONS = 5
    
    def create_conversation(
        self,
        db: Session,
        participant_ids: List[str],
        commodity: Optional[str] = None
    ) -> Tuple[bool, Optional[Conversation], Optional[str]]:
        """
        Create a new conversation.
        
        Requirements: 16.1, 16.2, 16.3
        
        Args:
            db: Database session
            participant_ids: List of participant user IDs
            commodity: Optional commodity being discussed
        
        Returns:
            Tuple of (success, conversation, error_message)
        """
        try:
            # Validate all participants exist
            participant_uuids = []
            for participant_id in participant_ids:
                try:
                    uuid_obj = UUID(participant_id)
                    participant_uuids.append(uuid_obj)
                except ValueError:
                    return False, None, f"Invalid UUID format: {participant_id}"
            
            # Check if all users exist
            users = db.query(User).filter(User.id.in_(participant_uuids)).all()
            if len(users) != len(participant_uuids):
                found_ids = {str(user.id) for user in users}
                missing_ids = set(participant_ids) - found_ids
                return False, None, f"Users not found: {', '.join(missing_ids)}"
            
            # Create conversation
            conversation = Conversation(
                participants=participant_uuids,
                commodity=commodity,
                status=ConversationStatus.ACTIVE
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Created conversation {conversation.id} with {len(participant_ids)} participants")
            return True, conversation, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating conversation: {str(e)}")
            return False, None, f"Failed to create conversation: {str(e)}"
    
    def get_user_conversations(
        self,
        db: Session,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> Tuple[bool, List[Conversation], Optional[str]]:
        """
        Get all conversations for a user.
        
        Requirements: 16.1, 16.2
        
        Args:
            db: Database session
            user_id: User ID
            status_filter: Optional status filter (active, completed, abandoned)
        
        Returns:
            Tuple of (success, conversations, error_message)
        """
        try:
            # Validate user ID
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                return False, [], f"Invalid UUID format: {user_id}"
            
            # Build query
            query = db.query(Conversation).filter(
                Conversation.participants.contains([user_uuid])
            )
            
            # Apply status filter if provided
            if status_filter:
                try:
                    status_enum = ConversationStatus(status_filter)
                    query = query.filter(Conversation.status == status_enum)
                except ValueError:
                    return False, [], f"Invalid status: {status_filter}"
            
            # Order by most recently updated
            conversations = query.order_by(desc(Conversation.updated_at)).all()
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return True, conversations, None
            
        except Exception as e:
            logger.error(f"Error retrieving conversations: {str(e)}")
            return False, [], f"Failed to retrieve conversations: {str(e)}"
    
    def get_conversation(
        self,
        db: Session,
        conversation_id: str,
        user_id: str
    ) -> Tuple[bool, Optional[Conversation], Optional[str]]:
        """
        Get a specific conversation.
        
        Requirements: 16.2, 16.3
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (to verify access)
        
        Returns:
            Tuple of (success, conversation, error_message)
        """
        try:
            # Validate IDs
            try:
                conv_uuid = UUID(conversation_id)
                user_uuid = UUID(user_id)
            except ValueError as e:
                return False, None, f"Invalid UUID format: {str(e)}"
            
            # Get conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conv_uuid
            ).first()
            
            if not conversation:
                return False, None, f"Conversation not found: {conversation_id}"
            
            # Verify user is a participant
            if user_uuid not in conversation.participants:
                return False, None, "User is not a participant in this conversation"
            
            return True, conversation, None
            
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            return False, None, f"Failed to retrieve conversation: {str(e)}"
    
    def update_conversation(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        commodity: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[bool, Optional[Conversation], Optional[str]]:
        """
        Update a conversation.
        
        Requirements: 16.1, 16.5
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (to verify access)
            commodity: Optional new commodity
            status: Optional new status
        
        Returns:
            Tuple of (success, conversation, error_message)
        """
        try:
            # Get conversation and verify access
            success, conversation, error = self.get_conversation(db, conversation_id, user_id)
            if not success:
                return False, None, error
            
            # Update fields
            if commodity is not None:
                conversation.commodity = commodity
            
            if status is not None:
                try:
                    conversation.status = ConversationStatus(status)
                except ValueError:
                    return False, None, f"Invalid status: {status}"
            
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Updated conversation {conversation_id}")
            return True, conversation, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating conversation: {str(e)}")
            return False, None, f"Failed to update conversation: {str(e)}"
    
    def end_conversation(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        final_status: str = "completed"
    ) -> Tuple[bool, Optional[str]]:
        """
        End a conversation by setting its status.
        
        Requirements: 16.5
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (to verify access)
            final_status: Final status (completed or abandoned)
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate final status
            if final_status not in ['completed', 'abandoned']:
                return False, "Final status must be 'completed' or 'abandoned'"
            
            # Update conversation status
            success, conversation, error = self.update_conversation(
                db, conversation_id, user_id, status=final_status
            )
            
            if not success:
                return False, error
            
            logger.info(f"Ended conversation {conversation_id} with status {final_status}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")
            return False, f"Failed to end conversation: {str(e)}"
    
    def send_message(
        self,
        db: Session,
        conversation_id: str,
        sender_id: str,
        original_text: str,
        original_language: str,
        translated_text: Optional[dict] = None,
        audio_url: Optional[str] = None,
        message_metadata: Optional[dict] = None
    ) -> Tuple[bool, Optional[Message], Optional[str]]:
        """
        Send a message in a conversation.
        
        Requirements: 16.3
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            sender_id: Sender user ID
            original_text: Original message text
            original_language: Language code
            translated_text: Optional translations
            audio_url: Optional audio URL
            message_metadata: Optional metadata
        
        Returns:
            Tuple of (success, message, error_message)
        """
        try:
            # Verify conversation exists and user is participant
            success, conversation, error = self.get_conversation(db, conversation_id, sender_id)
            if not success:
                return False, None, error
            
            # Verify conversation is active
            if conversation.status != ConversationStatus.ACTIVE:
                return False, None, f"Cannot send message to {conversation.status.value} conversation"
            
            # Validate sender ID
            try:
                sender_uuid = UUID(sender_id)
            except ValueError:
                return False, None, f"Invalid UUID format: {sender_id}"
            
            # Create message
            message = Message(
                conversation_id=UUID(conversation_id),
                sender_id=sender_uuid,
                original_text=original_text,
                original_language=original_language,
                translated_text=translated_text or {},
                audio_url=audio_url,
                message_metadata=message_metadata or {}
            )
            
            db.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(message)
            
            logger.info(f"Sent message {message.id} in conversation {conversation_id}")
            return True, message, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error sending message: {str(e)}")
            return False, None, f"Failed to send message: {str(e)}"
    
    def get_conversation_messages(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Tuple[bool, List[Message], int, Optional[str]]:
        """
        Get messages from a conversation.
        
        Requirements: 16.3
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (to verify access)
            limit: Optional limit on number of messages
            offset: Offset for pagination
        
        Returns:
            Tuple of (success, messages, total_count, error_message)
        """
        try:
            # Verify conversation exists and user is participant
            success, conversation, error = self.get_conversation(db, conversation_id, user_id)
            if not success:
                return False, [], 0, error
            
            # Get total count
            total_count = db.query(func.count(Message.id)).filter(
                Message.conversation_id == UUID(conversation_id)
            ).scalar()
            
            # Build query
            query = db.query(Message).filter(
                Message.conversation_id == UUID(conversation_id)
            ).order_by(Message.timestamp)
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            logger.info(f"Retrieved {len(messages)} messages from conversation {conversation_id}")
            return True, messages, total_count, None
            
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            return False, [], 0, f"Failed to retrieve messages: {str(e)}"
    
    def count_active_conversations(
        self,
        db: Session,
        user_id: str
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Count active conversations for a user.
        
        Requirements: 16.1
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Tuple of (success, count, error_message)
        """
        try:
            # Validate user ID
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                return False, 0, f"Invalid UUID format: {user_id}"
            
            # Count active conversations
            count = db.query(func.count(Conversation.id)).filter(
                Conversation.participants.contains([user_uuid]),
                Conversation.status == ConversationStatus.ACTIVE
            ).scalar()
            
            return True, count, None
            
        except Exception as e:
            logger.error(f"Error counting conversations: {str(e)}")
            return False, 0, f"Failed to count conversations: {str(e)}"
    
    def can_create_conversation(
        self,
        db: Session,
        user_id: str
    ) -> Tuple[bool, bool, Optional[str]]:
        """
        Check if user can create a new conversation (max 5 concurrent).
        
        Requirements: 16.1
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Tuple of (success, can_create, error_message)
        """
        try:
            success, count, error = self.count_active_conversations(db, user_id)
            if not success:
                return False, False, error
            
            can_create = count < self.MAX_CONCURRENT_CONVERSATIONS
            
            if not can_create:
                return True, False, f"Maximum of {self.MAX_CONCURRENT_CONVERSATIONS} concurrent conversations reached"
            
            return True, True, None
            
        except Exception as e:
            logger.error(f"Error checking conversation limit: {str(e)}")
            return False, False, f"Failed to check conversation limit: {str(e)}"
