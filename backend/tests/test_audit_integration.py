"""
Integration tests for audit logging across services

Tests that audit logging is properly integrated into:
- Authentication service
- STT service
- Translation service
- Transaction service

Requirements: 15.10
Property 54: Audit Log Maintenance
Property 45: Privacy-Preserving Error Logging
"""
import pytest
import numpy as np
from uuid import uuid4
from datetime import datetime

from app.services.auth.authentication_service import AuthenticationService
from app.services.vocal_vernacular.stt_service import STTService
from app.services.vocal_vernacular.translation_service import TranslationService
from app.services.transaction_service import TransactionService
from app.services.audit.audit_logger import AuditLogger
from app.models.user import User
from app.models.voiceprint import Voiceprint


class TestAuthenticationAuditLogging:
    """Test audit logging in authentication service"""
    
    def test_successful_voice_authentication_logged(self, db_session):
        """Test that successful voice authentication is logged"""
        # Create test user with voiceprint
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        voiceprint = Voiceprint(
            user_id=user.id,
            embedding=np.random.rand(192).tobytes(),
            sample_count=3
        )
        db_session.add(voiceprint)
        db_session.commit()
        
        # Attempt authentication (will fail but should log)
        auth_service = AuthenticationService()
        
        # Create mock audio data
        import base64
        audio_data = base64.b64encode(b"mock_audio_data").decode()
        
        # Authenticate
        success, user_result, error, confidence = auth_service.authenticate_with_voice(
            db=db_session,
            phone_number="1234567890",
            audio_data=audio_data,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="authentication",
            actor_id=user.id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        auth_log = logs[0]
        assert auth_log.event_type == "authentication"
        assert auth_log.action == "authenticate"
        assert auth_log.metadata["auth_method"] == "voice_biometric"
        assert auth_log.ip_address_anonymized == "192.168.1.x"
        assert auth_log.user_agent == "TestAgent/1.0"
    
    def test_failed_authentication_logged(self, db_session):
        """Test that failed authentication attempts are logged"""
        auth_service = AuthenticationService()
        
        # Create mock audio data
        import base64
        audio_data = base64.b64encode(b"mock_audio_data").decode()
        
        # Attempt authentication with non-existent user
        success, user, error, confidence = auth_service.authenticate_with_voice(
            db=db_session,
            phone_number="9999999999",
            audio_data=audio_data,
            ip_address="10.0.0.50",
            user_agent="TestAgent/1.0"
        )
        
        # Verify authentication failed
        assert not success
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="authentication",
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        auth_log = logs[0]
        assert auth_log.event_type == "authentication"
        assert auth_log.result == "failure"
        assert auth_log.metadata["reason"] == "user_not_found"
    
    def test_pin_authentication_logged(self, db_session):
        """Test that PIN authentication is logged"""
        # Create test user
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        auth_service = AuthenticationService()
        
        # Attempt PIN authentication
        success, user_result, error = auth_service.authenticate_with_pin(
            db=db_session,
            phone_number="1234567890",
            pin="1234",
            ip_address="172.16.0.1",
            user_agent="TestAgent/1.0"
        )
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="authentication",
            actor_id=user.id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        auth_log = logs[0]
        assert auth_log.event_type == "authentication"
        assert auth_log.metadata["auth_method"] == "pin"


class TestSTTAuditLogging:
    """Test audit logging in STT service"""
    
    def test_transcription_logged(self, db_session):
        """Test that transcription operations are logged"""
        stt_service = STTService(use_mock=True)
        
        # Create test user
        user_id = uuid4()
        
        # Create mock audio
        audio = np.random.rand(16000)  # 1 second of audio at 16kHz
        
        # Transcribe with audit logging
        result = stt_service.transcribe(
            audio=audio,
            language="hin",
            user_id=user_id,
            db=db_session,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Verify transcription succeeded
        assert result.text is not None
        assert result.confidence > 0
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_processing",
            actor_id=user_id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        stt_log = logs[0]
        assert stt_log.event_type == "data_processing"
        assert stt_log.event_category == "transcription"
        assert stt_log.action == "process"
        assert stt_log.metadata["language"] == "hin"
        assert "confidence" in stt_log.metadata
        assert "processing_time_ms" in stt_log.metadata
        assert stt_log.ip_address_anonymized == "192.168.1.x"
    
    def test_transcription_without_audit_logging(self, db_session):
        """Test that transcription works without audit logging parameters"""
        stt_service = STTService(use_mock=True)
        
        # Create mock audio
        audio = np.random.rand(16000)
        
        # Transcribe without audit logging
        result = stt_service.transcribe(
            audio=audio,
            language="hin"
        )
        
        # Verify transcription succeeded
        assert result.text is not None
        assert result.confidence > 0
        
        # Verify no audit logs were created
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_processing",
            limit=10
        )
        
        # Should be no logs since we didn't provide user_id and db
        assert len(logs) == 0


class TestTranslationAuditLogging:
    """Test audit logging in translation service"""
    
    def test_translation_logged(self, db_session):
        """Test that translation operations are logged"""
        # Note: This test requires the actual model to be loaded
        # For now, we'll skip if model is not available
        try:
            translation_service = TranslationService()
            translation_service.load_model()
        except Exception:
            pytest.skip("Translation model not available")
        
        # Create test user
        user_id = uuid4()
        
        # Translate with audit logging
        result = translation_service.translate(
            text="Hello, how are you?",
            source_lang="eng_Latn",
            target_lang="hin_Deva",
            user_id=user_id,
            db=db_session,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Verify translation succeeded
        assert result.text is not None
        assert result.confidence > 0
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_processing",
            actor_id=user_id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        trans_log = logs[0]
        assert trans_log.event_type == "data_processing"
        assert trans_log.event_category == "translation"
        assert trans_log.action == "process"
        assert trans_log.metadata["source_language"] == "eng_Latn"
        assert trans_log.metadata["target_language"] == "hin_Deva"
        assert "confidence" in trans_log.metadata
        assert "processing_time_ms" in trans_log.metadata


class TestTransactionAuditLogging:
    """Test audit logging in transaction service"""
    
    def test_transaction_creation_logged(self, db_session):
        """Test that transaction creation is logged"""
        # Create test users
        buyer = User(
            name="Buyer",
            phone_number="1111111111",
            primary_language="hin"
        )
        seller = User(
            name="Seller",
            phone_number="2222222222",
            primary_language="tel"
        )
        db_session.add(buyer)
        db_session.add(seller)
        db_session.commit()
        
        # Create transaction
        transaction_service = TransactionService()
        success, transaction, error = transaction_service.create_transaction(
            db=db_session,
            buyer_id=str(buyer.id),
            seller_id=str(seller.id),
            commodity="tomato",
            quantity=10.0,
            unit="kg",
            agreed_price=25.0,
            market_average_at_time=24.0,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Verify transaction created
        assert success
        assert transaction is not None
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_access",
            actor_id=buyer.id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        txn_log = logs[0]
        assert txn_log.event_type == "data_access"
        assert txn_log.event_category == "transaction"
        assert txn_log.action == "create"
        assert txn_log.result == "success"
        assert txn_log.metadata["commodity"] == "tomato"
        assert txn_log.metadata["quantity"] == 10.0
        assert txn_log.metadata["unit"] == "kg"
        assert txn_log.ip_address_anonymized == "192.168.1.x"
    
    def test_transaction_history_access_logged(self, db_session):
        """Test that transaction history access is logged"""
        # Create test user
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        # Access transaction history
        transaction_service = TransactionService()
        success, transactions, total_count, error = transaction_service.get_user_transaction_history(
            db=db_session,
            user_id=str(user.id),
            limit=5,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Verify access succeeded
        assert success
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_access",
            actor_id=user.id,
            limit=10
        )
        
        # Verify audit log was created
        assert len(logs) >= 1
        history_log = logs[0]
        assert history_log.event_type == "data_access"
        assert history_log.event_category == "transaction"
        assert history_log.action == "list"
        assert history_log.result == "success"
        assert "record_count" in history_log.metadata
        assert history_log.ip_address_anonymized == "192.168.1.x"


class TestAuditLogPrivacy:
    """Test that audit logs don't contain PII"""
    
    def test_no_pii_in_authentication_logs(self, db_session):
        """Test that authentication logs don't contain PII"""
        auth_service = AuthenticationService()
        
        # Create mock audio data
        import base64
        audio_data = base64.b64encode(b"mock_audio_data").decode()
        
        # Attempt authentication
        auth_service.authenticate_with_voice(
            db=db_session,
            phone_number="1234567890",
            audio_data=audio_data,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="authentication",
            limit=10
        )
        
        # Verify no PII in logs
        for log in logs:
            assert audit_logger.verify_no_pii_in_logs(log)
            # Verify phone number is not in metadata
            if log.metadata:
                for key, value in log.metadata.items():
                    assert "1234567890" not in str(value)
    
    def test_no_pii_in_transaction_logs(self, db_session):
        """Test that transaction logs don't contain PII"""
        # Create test users
        buyer = User(
            name="John Doe",
            phone_number="1111111111",
            primary_language="hin"
        )
        seller = User(
            name="Jane Smith",
            phone_number="2222222222",
            primary_language="tel"
        )
        db_session.add(buyer)
        db_session.add(seller)
        db_session.commit()
        
        # Create transaction
        transaction_service = TransactionService()
        transaction_service.create_transaction(
            db=db_session,
            buyer_id=str(buyer.id),
            seller_id=str(seller.id),
            commodity="tomato",
            quantity=10.0,
            unit="kg",
            agreed_price=25.0,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(
            event_type="data_access",
            limit=10
        )
        
        # Verify no PII in logs
        for log in logs:
            assert audit_logger.verify_no_pii_in_logs(log)
            # Verify names and phone numbers are not in metadata
            if log.metadata:
                metadata_str = str(log.metadata)
                assert "John Doe" not in metadata_str
                assert "Jane Smith" not in metadata_str
                assert "1111111111" not in metadata_str
                assert "2222222222" not in metadata_str
    
    def test_ip_addresses_anonymized(self, db_session):
        """Test that IP addresses are anonymized in all logs"""
        # Create test user
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create various operations with IP addresses
        transaction_service = TransactionService()
        transaction_service.get_user_transaction_history(
            db=db_session,
            user_id=str(user.id),
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        
        # Query audit logs
        audit_logger = AuditLogger(db_session)
        logs = audit_logger.query_audit_logs(limit=10)
        
        # Verify all IP addresses are anonymized
        for log in logs:
            if log.ip_address_anonymized:
                # Should not contain full IP
                assert "192.168.1.100" not in log.ip_address_anonymized
                # Should be anonymized
                assert log.ip_address_anonymized == "192.168.1.x"


class TestAuditLogQuerying:
    """Test audit log querying functionality"""
    
    def test_query_by_event_type(self, db_session):
        """Test querying audit logs by event type"""
        # Create test user
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create different types of audit logs
        audit_logger = AuditLogger(db_session)
        
        audit_logger.log_authentication(
            actor_id=user.id,
            auth_method="voice_biometric",
            result="success"
        )
        
        audit_logger.log_data_access(
            resource_type="transaction",
            actor_id=user.id,
            action="read",
            result="success"
        )
        
        # Query by event type
        auth_logs = audit_logger.query_audit_logs(event_type="authentication")
        access_logs = audit_logger.query_audit_logs(event_type="data_access")
        
        # Verify filtering works
        assert len(auth_logs) >= 1
        assert len(access_logs) >= 1
        assert all(log.event_type == "authentication" for log in auth_logs)
        assert all(log.event_type == "data_access" for log in access_logs)
    
    def test_query_by_actor(self, db_session):
        """Test querying audit logs by actor"""
        # Create test users
        user1 = User(
            name="User 1",
            phone_number="1111111111",
            primary_language="hin"
        )
        user2 = User(
            name="User 2",
            phone_number="2222222222",
            primary_language="tel"
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Create audit logs for different users
        audit_logger = AuditLogger(db_session)
        
        audit_logger.log_data_access(
            resource_type="transaction",
            actor_id=user1.id,
            action="read",
            result="success"
        )
        
        audit_logger.log_data_access(
            resource_type="transaction",
            actor_id=user2.id,
            action="read",
            result="success"
        )
        
        # Query by actor
        user1_logs = audit_logger.query_audit_logs(actor_id=user1.id)
        user2_logs = audit_logger.query_audit_logs(actor_id=user2.id)
        
        # Verify filtering works
        assert len(user1_logs) >= 1
        assert len(user2_logs) >= 1
        
        # Verify all logs belong to correct user (by checking hash)
        user1_hash = audit_logger._hash_identifier(user1.id)
        user2_hash = audit_logger._hash_identifier(user2.id)
        
        assert all(log.actor_id_hash == user1_hash for log in user1_logs)
        assert all(log.actor_id_hash == user2_hash for log in user2_logs)
    
    def test_query_by_date_range(self, db_session):
        """Test querying audit logs by date range"""
        from datetime import timedelta
        
        # Create test user
        user = User(
            name="Test User",
            phone_number="1234567890",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create audit log
        audit_logger = AuditLogger(db_session)
        audit_logger.log_data_access(
            resource_type="transaction",
            actor_id=user.id,
            action="read",
            result="success"
        )
        
        # Query with date range
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now + timedelta(hours=1)
        
        logs = audit_logger.query_audit_logs(
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify logs are within date range
        assert len(logs) >= 1
        for log in logs:
            assert start_date <= log.timestamp <= end_date
