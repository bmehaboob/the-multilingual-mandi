"""
Unit tests for Account Deletion Service

Tests the account deletion service functionality including:
- Requesting account deletion
- Cancelling deletion requests
- Executing account deletion
- Getting deletion status

Requirements: 15.4 - Account deletion with data removal within 30 days
Property 49: Account Deletion Data Removal
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.privacy.account_deletion_service import AccountDeletionService
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.models.user_preferences import UserPreferences
from app.models.conversation import Conversation, Message, ConversationStatus
from app.models.transaction import Transaction


@pytest.fixture
def deletion_service():
    """Create account deletion service instance"""
    return AccountDeletionService()


@pytest.fixture
def test_user(db: Session):
    """Create a test user with associated data"""
    user = User(
        id=uuid4(),
        name="Test User",
        phone_number="+919876543210",
        primary_language="hi",
        secondary_languages=["en"],
        location={"state": "Maharashtra", "district": "Mumbai"},
        preferences={}
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_with_data(db: Session, test_user: User):
    """Create a test user with voiceprint, preferences, messages, and transactions"""
    # Add voiceprint
    voiceprint = Voiceprint(
        id=uuid4(),
        user_id=test_user.id,
        embedding_data=b"fake_embedding_data",
        encryption_algorithm="AES-256",
        sample_count=3
    )
    db.add(voiceprint)
    
    # Add user preferences
    preferences = UserPreferences(
        id=uuid4(),
        user_id=test_user.id,
        speech_rate=0.85,
        volume_boost=False,
        offline_mode=False,
        favorite_contacts=[]
    )
    db.add(preferences)
    
    # Add conversation and messages
    conversation = Conversation(
        id=uuid4(),
        participants=[str(test_user.id)],
        commodity="tomato",
        status=ConversationStatus.ACTIVE
    )
    db.add(conversation)
    db.commit()
    
    message = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        sender_id=test_user.id,
        original_text="Hello",
        original_language="hi",
        translated_text={"en": "Hello"}
    )
    db.add(message)
    
    # Add transaction
    other_user = User(
        id=uuid4(),
        name="Other User",
        phone_number="+919876543211",
        primary_language="te",
        preferences={}
    )
    db.add(other_user)
    db.commit()
    
    transaction = Transaction(
        id=uuid4(),
        buyer_id=test_user.id,
        seller_id=other_user.id,
        commodity="tomato",
        quantity=10.0,
        unit="kg",
        agreed_price=200.0,
        market_average_at_time=195.0,
        conversation_id=conversation.id,
        location={"state": "Maharashtra"}
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(test_user)
    
    return test_user


class TestAccountDeletionRequest:
    """Tests for requesting account deletion"""
    
    def test_request_deletion_success(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test successful account deletion request"""
        result = deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id),
            reason="No longer needed"
        )
        
        assert result["user_id"] == str(test_user.id)
        assert result["status"] == "pending_deletion"
        assert result["grace_period_days"] == 30
        assert "deletion_requested_at" in result
        assert "deletion_scheduled_for" in result
        
        # Verify user preferences updated
        db.refresh(test_user)
        assert test_user.preferences["deletion_requested"] is True
        assert test_user.preferences["account_disabled"] is True
        assert test_user.preferences["deletion_reason"] == "No longer needed"
    
    def test_request_deletion_without_reason(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test deletion request without reason"""
        result = deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        assert result["status"] == "pending_deletion"
        db.refresh(test_user)
        assert "deletion_reason" not in test_user.preferences
    
    def test_request_deletion_user_not_found(
        self,
        db: Session,
        deletion_service: AccountDeletionService
    ):
        """Test deletion request for non-existent user"""
        fake_user_id = str(uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            deletion_service.request_account_deletion(
                db=db,
                user_id=fake_user_id
            )
    
    def test_request_deletion_already_requested(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test requesting deletion when already requested"""
        # First request
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Second request should fail
        with pytest.raises(ValueError, match="already marked for deletion"):
            deletion_service.request_account_deletion(
                db=db,
                user_id=str(test_user.id)
            )
    
    def test_deletion_scheduled_date(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test that deletion is scheduled 30 days in the future"""
        result = deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        scheduled_date = datetime.fromisoformat(result["deletion_scheduled_for"])
        expected_date = datetime.utcnow() + timedelta(days=30)
        
        # Allow 1 minute tolerance for test execution time
        time_diff = abs((scheduled_date - expected_date).total_seconds())
        assert time_diff < 60


class TestDeletionCancellation:
    """Tests for cancelling deletion requests"""
    
    def test_cancel_deletion_success(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test successful deletion cancellation"""
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Cancel deletion
        result = deletion_service.cancel_deletion_request(
            db=db,
            user_id=str(test_user.id)
        )
        
        assert result["user_id"] == str(test_user.id)
        assert result["status"] == "active"
        assert "cancelled_at" in result
        
        # Verify user preferences updated
        db.refresh(test_user)
        assert test_user.preferences["deletion_requested"] is False
        assert test_user.preferences["account_disabled"] is False
        assert "deletion_history" in test_user.preferences
    
    def test_cancel_deletion_no_request(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test cancelling when no deletion requested"""
        with pytest.raises(ValueError, match="No deletion request pending"):
            deletion_service.cancel_deletion_request(
                db=db,
                user_id=str(test_user.id)
            )
    
    def test_cancel_deletion_user_not_found(
        self,
        db: Session,
        deletion_service: AccountDeletionService
    ):
        """Test cancellation for non-existent user"""
        fake_user_id = str(uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            deletion_service.cancel_deletion_request(
                db=db,
                user_id=fake_user_id
            )


class TestAccountDeletionExecution:
    """Tests for executing account deletion"""
    
    def test_execute_deletion_success(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user_with_data: User
    ):
        """Test successful account deletion execution"""
        user_id = str(test_user_with_data.id)
        
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=user_id
        )
        
        # Execute deletion with force=True to bypass grace period
        result = deletion_service.execute_account_deletion(
            db=db,
            user_id=user_id,
            force=True
        )
        
        assert result["user_id"] == user_id
        assert "deleted_at" in result
        assert "data_removed" in result
        assert len(result["data_removed"]) > 0
        
        # Verify user is deleted
        user = db.query(User).filter(User.id == user_id).first()
        assert user is None
        
        # Verify voiceprint is deleted
        voiceprint = db.query(Voiceprint).filter(
            Voiceprint.user_id == user_id
        ).first()
        assert voiceprint is None
        
        # Verify preferences are deleted
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        assert preferences is None
        
        # Verify messages are deleted
        messages = db.query(Message).filter(
            Message.sender_id == user_id
        ).all()
        assert len(messages) == 0
    
    def test_execute_deletion_without_request(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test executing deletion without prior request"""
        with pytest.raises(ValueError, match="No deletion request found"):
            deletion_service.execute_account_deletion(
                db=db,
                user_id=str(test_user.id),
                force=False
            )
    
    def test_execute_deletion_grace_period_not_elapsed(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test executing deletion before grace period"""
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Try to execute without force (should fail)
        with pytest.raises(ValueError, match="Grace period not elapsed"):
            deletion_service.execute_account_deletion(
                db=db,
                user_id=str(test_user.id),
                force=False
            )
    
    def test_execute_deletion_force_bypass(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test force flag bypasses grace period"""
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Execute with force=True should succeed
        result = deletion_service.execute_account_deletion(
            db=db,
            user_id=str(test_user.id),
            force=True
        )
        
        assert result["user_id"] == str(test_user.id)
    
    def test_transaction_anonymization(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user_with_data: User
    ):
        """Test that transactions are anonymized, not deleted"""
        user_id = str(test_user_with_data.id)
        
        # Get transaction count before deletion
        transactions_before = db.query(Transaction).filter(
            Transaction.buyer_id == user_id
        ).count()
        assert transactions_before > 0
        
        # Execute deletion
        deletion_service.request_account_deletion(db=db, user_id=user_id)
        deletion_service.execute_account_deletion(db=db, user_id=user_id, force=True)
        
        # Verify transactions still exist but are anonymized
        anonymized_id = "00000000-0000-0000-0000-000000000000"
        transactions_after = db.query(Transaction).filter(
            Transaction.buyer_id == anonymized_id
        ).count()
        assert transactions_after == transactions_before


class TestDeletionStatus:
    """Tests for getting deletion status"""
    
    def test_get_status_active_account(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test status for active account"""
        status = deletion_service.get_deletion_status(
            db=db,
            user_id=str(test_user.id)
        )
        
        assert status["user_id"] == str(test_user.id)
        assert status["status"] == "active"
        assert status["deletion_requested"] is False
    
    def test_get_status_pending_deletion(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test status for account pending deletion"""
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        status = deletion_service.get_deletion_status(
            db=db,
            user_id=str(test_user.id)
        )
        
        assert status["status"] == "pending_deletion"
        assert status["deletion_requested"] is True
        assert "deletion_requested_at" in status
        assert "deletion_scheduled_for" in status
        assert "days_remaining" in status
        assert status["can_cancel"] is True
        assert status["days_remaining"] >= 29  # Should be close to 30
    
    def test_get_status_user_not_found(
        self,
        db: Session,
        deletion_service: AccountDeletionService
    ):
        """Test status for non-existent user"""
        fake_user_id = str(uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            deletion_service.get_deletion_status(
                db=db,
                user_id=fake_user_id
            )


class TestPendingDeletions:
    """Tests for getting pending deletions"""
    
    def test_get_pending_deletions_none(
        self,
        db: Session,
        deletion_service: AccountDeletionService
    ):
        """Test when no deletions are pending"""
        pending = deletion_service.get_pending_deletions(db=db)
        assert len(pending) == 0
    
    def test_get_pending_deletions_with_pending(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test getting pending deletions"""
        # Request deletion
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Manually set scheduled date to past
        test_user.preferences["deletion_scheduled_for"] = (
            datetime.utcnow() - timedelta(days=1)
        ).isoformat()
        db.commit()
        
        # Get pending deletions
        pending = deletion_service.get_pending_deletions(db=db)
        
        assert len(pending) == 1
        assert pending[0]["user_id"] == str(test_user.id)
        assert pending[0]["name"] == test_user.name
    
    def test_get_pending_deletions_filters_future(
        self,
        db: Session,
        deletion_service: AccountDeletionService,
        test_user: User
    ):
        """Test that future deletions are not included"""
        # Request deletion (scheduled 30 days in future)
        deletion_service.request_account_deletion(
            db=db,
            user_id=str(test_user.id)
        )
        
        # Get pending deletions (should be empty)
        pending = deletion_service.get_pending_deletions(db=db)
        assert len(pending) == 0
