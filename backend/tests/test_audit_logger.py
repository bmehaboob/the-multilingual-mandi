"""
Unit tests for Audit Logger Service

Tests the audit logging functionality including:
- Data access logging
- Data processing logging
- Data export logging
- Data deletion logging
- Authentication logging
- PII sanitization
- IP address anonymization
- Query functionality

Requirements: 15.10
Property 54: Audit Log Maintenance
Property 45: Privacy-Preserving Error Logging
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.audit.audit_logger import AuditLogger
from app.models.audit_log import AuditLog


class TestAuditLogger:
    """Test suite for AuditLogger service"""
    
    def test_log_data_access_success(self, db_session):
        """Test logging a successful data access operation"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        resource_id = uuid4()
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            resource_id=resource_id,
            actor_id=user_id,
            action="read",
            result="success",
            metadata={"record_count": 1},
            description="User profile accessed",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        assert audit_log is not None
        assert audit_log.event_type == "data_access"
        assert audit_log.event_category == "user"
        assert audit_log.action == "read"
        assert audit_log.resource_type == "user"
        assert audit_log.result == "success"
        assert audit_log.metadata["record_count"] == 1
        assert audit_log.description == "User profile accessed"
        
        # Verify IDs are hashed
        assert audit_log.resource_id_hash != str(resource_id)
        assert audit_log.actor_id_hash != str(user_id)
        assert len(audit_log.resource_id_hash) == 64  # SHA-256 hex length
        assert len(audit_log.actor_id_hash) == 64
        
        # Verify IP is anonymized
        assert audit_log.ip_address_anonymized == "192.168.1.x"
        
        # Verify user agent is stored
        assert audit_log.user_agent == "Mozilla/5.0"
    
    def test_log_data_processing(self, db_session):
        """Test logging a data processing operation"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        message_id = uuid4()
        
        audit_log = audit_logger.log_data_processing(
            operation="transcription",
            resource_type="audio",
            resource_id=message_id,
            actor_id=user_id,
            result="success",
            metadata={
                "language": "hi",
                "duration_ms": 1500,
                "confidence": 0.95
            },
            description="Audio transcribed to text"
        )
        
        assert audit_log is not None
        assert audit_log.event_type == "data_processing"
        assert audit_log.event_category == "transcription"
        assert audit_log.action == "process"
        assert audit_log.result == "success"
        assert audit_log.metadata["language"] == "hi"
        assert audit_log.metadata["duration_ms"] == 1500
        assert audit_log.metadata["confidence"] == 0.95
    
    def test_log_data_export(self, db_session):
        """Test logging a data export operation"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        audit_log = audit_logger.log_data_export(
            resource_type="transaction",
            actor_id=user_id,
            record_count=25,
            result="success",
            metadata={"format": "json"},
            description="User exported transaction history"
        )
        
        assert audit_log is not None
        assert audit_log.event_type == "data_export"
        assert audit_log.event_category == "transaction"
        assert audit_log.action == "export"
        assert audit_log.result == "success"
        assert audit_log.metadata["record_count"] == 25
        assert audit_log.metadata["format"] == "json"
    
    def test_log_data_deletion(self, db_session):
        """Test logging a data deletion operation"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        resource_id = uuid4()
        
        audit_log = audit_logger.log_data_deletion(
            resource_type="user",
            resource_id=resource_id,
            actor_id=user_id,
            result="success",
            metadata={"deletion_type": "account_deletion"},
            description="User account deleted"
        )
        
        assert audit_log is not None
        assert audit_log.event_type == "data_deletion"
        assert audit_log.event_category == "user"
        assert audit_log.action == "delete"
        assert audit_log.result == "success"
        assert audit_log.metadata["deletion_type"] == "account_deletion"
    
    def test_log_authentication_success(self, db_session):
        """Test logging a successful authentication"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        audit_log = audit_logger.log_authentication(
            actor_id=user_id,
            auth_method="voice_biometric",
            result="success",
            metadata={"confidence": 0.97},
            description="User authenticated via voice",
            ip_address="10.0.0.50"
        )
        
        assert audit_log is not None
        assert audit_log.event_type == "authentication"
        assert audit_log.event_category == "user_auth"
        assert audit_log.action == "authenticate"
        assert audit_log.result == "success"
        assert audit_log.metadata["auth_method"] == "voice_biometric"
        assert audit_log.metadata["confidence"] == 0.97
        assert audit_log.ip_address_anonymized == "10.0.0.x"
    
    def test_log_authentication_failure(self, db_session):
        """Test logging a failed authentication"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        audit_log = audit_logger.log_authentication(
            actor_id=user_id,
            auth_method="voice_biometric",
            result="failure",
            metadata={"reason": "low_confidence", "confidence": 0.65},
            description="Authentication failed due to low confidence"
        )
        
        assert audit_log is not None
        assert audit_log.result == "failure"
        assert audit_log.metadata["reason"] == "low_confidence"
    
    def test_pii_sanitization_in_metadata(self, db_session):
        """Test that PII is removed from metadata"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Metadata with PII fields
        metadata_with_pii = {
            "operation": "update",
            "name": "John Doe",  # PII
            "phone_number": "1234567890",  # PII
            "email": "john@example.com",  # PII
            "record_count": 1
        }
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
            action="update",
            result="success",
            metadata=metadata_with_pii
        )
        
        # Verify PII fields are redacted
        assert audit_log.metadata["name"] == "[REDACTED]"
        assert audit_log.metadata["phone_number"] == "[REDACTED]"
        assert audit_log.metadata["email"] == "[REDACTED]"
        
        # Verify non-PII fields are preserved
        assert audit_log.metadata["operation"] == "update"
        assert audit_log.metadata["record_count"] == 1
    
    def test_nested_pii_sanitization(self, db_session):
        """Test that PII is removed from nested metadata"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Nested metadata with PII
        metadata = {
            "operation": "create",
            "user_data": {
                "name": "Jane Doe",  # PII
                "language": "hi",
                "location": {
                    "state": "Maharashtra",
                    "address": "123 Main St"  # PII
                }
            }
        }
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
            action="create",
            result="success",
            metadata=metadata
        )
        
        # Verify nested PII is redacted
        assert audit_log.metadata["user_data"]["name"] == "[REDACTED]"
        assert audit_log.metadata["user_data"]["location"]["address"] == "[REDACTED]"
        
        # Verify non-PII is preserved
        assert audit_log.metadata["operation"] == "create"
        assert audit_log.metadata["user_data"]["language"] == "hi"
        assert audit_log.metadata["user_data"]["location"]["state"] == "Maharashtra"
    
    def test_ip_address_anonymization_ipv4(self, db_session):
        """Test IPv4 address anonymization"""
        audit_logger = AuditLogger(db_session)
        
        test_cases = [
            ("192.168.1.100", "192.168.1.x"),
            ("10.0.0.50", "10.0.0.x"),
            ("172.16.254.1", "172.16.254.x"),
        ]
        
        for ip_input, expected_output in test_cases:
            result = audit_logger._anonymize_ip_address(ip_input)
            assert result == expected_output, f"Failed for {ip_input}"
    
    def test_ip_address_anonymization_ipv6(self, db_session):
        """Test IPv6 address anonymization"""
        audit_logger = AuditLogger(db_session)
        
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        result = audit_logger._anonymize_ip_address(ipv6)
        
        assert result.startswith("2001:0db8:85a3:")
        assert result.endswith(":x:x:x:x:x")
    
    def test_ip_address_anonymization_none(self, db_session):
        """Test that None IP address is handled"""
        audit_logger = AuditLogger(db_session)
        
        result = audit_logger._anonymize_ip_address(None)
        assert result is None
    
    def test_hash_identifier_consistency(self, db_session):
        """Test that hashing the same identifier produces the same hash"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        hash1 = audit_logger._hash_identifier(user_id)
        hash2 = audit_logger._hash_identifier(user_id)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
    
    def test_hash_identifier_different_ids(self, db_session):
        """Test that different identifiers produce different hashes"""
        audit_logger = AuditLogger(db_session)
        
        user_id1 = uuid4()
        user_id2 = uuid4()
        
        hash1 = audit_logger._hash_identifier(user_id1)
        hash2 = audit_logger._hash_identifier(user_id2)
        
        assert hash1 != hash2
    
    def test_query_audit_logs_by_event_type(self, db_session):
        """Test querying audit logs by event type"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Create logs of different types
        audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
            action="read",
            result="success"
        )
        
        audit_logger.log_data_processing(
            operation="transcription",
            resource_type="audio",
            actor_id=user_id,
            result="success"
        )
        
        audit_logger.log_authentication(
            actor_id=user_id,
            auth_method="voice_biometric",
            result="success"
        )
        
        # Query for data_access events
        logs = audit_logger.query_audit_logs(event_type="data_access")
        assert len(logs) == 1
        assert logs[0].event_type == "data_access"
        
        # Query for authentication events
        logs = audit_logger.query_audit_logs(event_type="authentication")
        assert len(logs) == 1
        assert logs[0].event_type == "authentication"
    
    def test_query_audit_logs_by_actor(self, db_session):
        """Test querying audit logs by actor"""
        audit_logger = AuditLogger(db_session)
        
        user_id1 = uuid4()
        user_id2 = uuid4()
        
        # Create logs for different users
        audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id1,
            action="read",
            result="success"
        )
        
        audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id1,
            action="update",
            result="success"
        )
        
        audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id2,
            action="read",
            result="success"
        )
        
        # Query for user1's logs
        logs = audit_logger.query_audit_logs(actor_id=user_id1)
        assert len(logs) == 2
        
        # Query for user2's logs
        logs = audit_logger.query_audit_logs(actor_id=user_id2)
        assert len(logs) == 1
    
    def test_query_audit_logs_by_date_range(self, db_session):
        """Test querying audit logs by date range"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Create a log
        audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
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
        
        assert len(logs) >= 1
        
        # Query with date range that excludes the log
        old_start = now - timedelta(days=2)
        old_end = now - timedelta(days=1)
        
        logs = audit_logger.query_audit_logs(
            start_date=old_start,
            end_date=old_end
        )
        
        assert len(logs) == 0
    
    def test_query_audit_logs_with_limit(self, db_session):
        """Test querying audit logs with limit"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Create multiple logs
        for i in range(10):
            audit_logger.log_data_access(
                resource_type="user",
                actor_id=user_id,
                action="read",
                result="success"
            )
        
        # Query with limit
        logs = audit_logger.query_audit_logs(limit=5)
        assert len(logs) == 5
    
    def test_verify_no_pii_in_logs_clean(self, db_session):
        """Test PII verification for clean logs"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
            action="read",
            result="success",
            metadata={"record_count": 1, "operation": "read"}
        )
        
        # Verify no PII
        assert audit_logger.verify_no_pii_in_logs(audit_log) is True
    
    def test_verify_no_pii_in_logs_with_pii(self, db_session):
        """Test PII verification detects PII in metadata"""
        audit_logger = AuditLogger(db_session)
        
        # Manually create an audit log with PII (bypassing sanitization)
        audit_log = AuditLog(
            event_type="data_access",
            event_category="user",
            action="read",
            resource_type="user",
            result="success",
            metadata={"name": "John Doe"}  # PII field
        )
        
        # Verify PII is detected
        assert audit_logger.verify_no_pii_in_logs(audit_log) is False
    
    def test_user_agent_truncation(self, db_session):
        """Test that long user agent strings are truncated"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        
        # Create a very long user agent string
        long_user_agent = "A" * 1000
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            actor_id=user_id,
            action="read",
            result="success",
            user_agent=long_user_agent
        )
        
        # Verify it's truncated to 500 characters
        assert len(audit_log.user_agent) == 500
    
    def test_log_without_optional_fields(self, db_session):
        """Test logging with minimal required fields"""
        audit_logger = AuditLogger(db_session)
        
        audit_log = audit_logger.log_data_access(
            resource_type="user",
            action="read",
            result="success"
        )
        
        assert audit_log is not None
        assert audit_log.resource_id_hash is None
        assert audit_log.actor_id_hash is None
        assert audit_log.event_metadata == {}
        assert audit_log.description is None
        assert audit_log.ip_address_anonymized is None
        assert audit_log.user_agent is None
    
    def test_multiple_operations_same_resource(self, db_session):
        """Test logging multiple operations on the same resource"""
        audit_logger = AuditLogger(db_session)
        
        user_id = uuid4()
        resource_id = uuid4()
        
        # Create multiple logs for the same resource
        audit_logger.log_data_access(
            resource_type="user",
            resource_id=resource_id,
            actor_id=user_id,
            action="read",
            result="success"
        )
        
        audit_logger.log_data_access(
            resource_type="user",
            resource_id=resource_id,
            actor_id=user_id,
            action="update",
            result="success"
        )
        
        audit_logger.log_data_deletion(
            resource_type="user",
            resource_id=resource_id,
            actor_id=user_id,
            result="success"
        )
        
        # Query all logs
        logs = audit_logger.query_audit_logs(actor_id=user_id)
        assert len(logs) == 3
        
        # Verify all have the same hashed resource ID
        resource_hashes = [log.resource_id_hash for log in logs if log.resource_id_hash]
        assert len(set(resource_hashes)) == 1  # All should be the same hash
