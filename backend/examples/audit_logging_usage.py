"""
Audit Logging Usage Examples

This file demonstrates how to integrate audit logging into various
services and API endpoints.

Requirements: 15.10
"""
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.audit.audit_logger import AuditLogger


# Example 1: Logging user authentication
def example_authentication_logging(db: Session):
    """Example of logging authentication attempts"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    # Successful authentication
    audit_logger.log_authentication(
        actor_id=user_id,
        auth_method="voice_biometric",
        result="success",
        metadata={
            "confidence": 0.97,
            "attempt_number": 1
        },
        description="User authenticated successfully via voice biometric",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Mobile)"
    )
    
    # Failed authentication
    audit_logger.log_authentication(
        actor_id=user_id,
        auth_method="voice_biometric",
        result="failure",
        metadata={
            "confidence": 0.65,
            "attempt_number": 2,
            "reason": "low_confidence"
        },
        description="Authentication failed due to low confidence score",
        ip_address="192.168.1.100"
    )


# Example 2: Logging data access operations
def example_data_access_logging(db: Session):
    """Example of logging data access operations"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    transaction_id = uuid4()
    
    # User viewing their transaction history
    audit_logger.log_data_access(
        resource_type="transaction",
        resource_id=transaction_id,
        actor_id=user_id,
        action="read",
        result="success",
        metadata={
            "record_count": 1,
            "query_type": "by_id"
        },
        description="User accessed transaction details",
        ip_address="10.0.0.50"
    )
    
    # User listing all their transactions
    audit_logger.log_data_access(
        resource_type="transaction",
        actor_id=user_id,
        action="list",
        result="success",
        metadata={
            "record_count": 25,
            "query_type": "by_user",
            "date_range_days": 90
        },
        description="User listed transaction history"
    )


# Example 3: Logging data processing operations
def example_data_processing_logging(db: Session):
    """Example of logging data processing operations"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    message_id = uuid4()
    
    # Speech-to-text processing
    audit_logger.log_data_processing(
        operation="transcription",
        resource_type="audio",
        resource_id=message_id,
        actor_id=user_id,
        result="success",
        metadata={
            "language": "hi",
            "duration_ms": 1500,
            "confidence": 0.95,
            "model": "indic-whisper"
        },
        description="Audio transcribed to text"
    )
    
    # Translation processing
    audit_logger.log_data_processing(
        operation="translation",
        resource_type="message",
        resource_id=message_id,
        actor_id=user_id,
        result="success",
        metadata={
            "source_language": "hi",
            "target_language": "te",
            "confidence": 0.98,
            "model": "indictrans2"
        },
        description="Message translated from Hindi to Telugu"
    )
    
    # Text-to-speech processing
    audit_logger.log_data_processing(
        operation="synthesis",
        resource_type="message",
        resource_id=message_id,
        actor_id=user_id,
        result="success",
        metadata={
            "language": "te",
            "duration_ms": 2000,
            "model": "indic-tts"
        },
        description="Text synthesized to speech"
    )


# Example 4: Logging data export operations
def example_data_export_logging(db: Session):
    """Example of logging data export operations"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    # User exporting their data
    audit_logger.log_data_export(
        resource_type="user_data",
        actor_id=user_id,
        record_count=150,
        result="success",
        metadata={
            "format": "json",
            "includes": ["transactions", "messages", "preferences"],
            "file_size_bytes": 52480
        },
        description="User exported personal data for DPDP compliance",
        ip_address="192.168.1.100"
    )
    
    # Admin exporting anonymized data for analysis
    admin_id = uuid4()
    audit_logger.log_data_export(
        resource_type="transaction",
        actor_id=admin_id,
        record_count=1000,
        result="success",
        metadata={
            "format": "csv",
            "anonymized": True,
            "date_range": "2024-01-01 to 2024-01-31"
        },
        description="Admin exported anonymized transaction data for market analysis"
    )


# Example 5: Logging data deletion operations
def example_data_deletion_logging(db: Session):
    """Example of logging data deletion operations"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    # Audio file deletion (automatic cleanup)
    audio_id = uuid4()
    audit_logger.log_data_deletion(
        resource_type="audio",
        resource_id=audio_id,
        actor_id=None,  # System operation
        result="success",
        metadata={
            "deletion_type": "automatic_cleanup",
            "age_hours": 24,
            "file_size_bytes": 15360
        },
        description="Audio file automatically deleted after 24 hours"
    )
    
    # User account deletion
    audit_logger.log_data_deletion(
        resource_type="user",
        resource_id=user_id,
        actor_id=user_id,
        result="success",
        metadata={
            "deletion_type": "account_deletion",
            "grace_period_days": 30,
            "data_removed": [
                "user_account",
                "voiceprints: 1",
                "messages: 45",
                "transactions: 12 anonymized"
            ]
        },
        description="User account and personal data deleted per DPDP Act"
    )


# Example 6: Logging with error handling
def example_error_handling_logging(db: Session):
    """Example of logging operations with error handling"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    try:
        # Simulate an operation that might fail
        # ... perform operation ...
        
        # Log success
        audit_logger.log_data_processing(
            operation="transcription",
            resource_type="audio",
            actor_id=user_id,
            result="success",
            metadata={"duration_ms": 1200}
        )
    except Exception as e:
        # Log failure
        audit_logger.log_data_processing(
            operation="transcription",
            resource_type="audio",
            actor_id=user_id,
            result="failure",
            metadata={
                "error_type": type(e).__name__,
                "error_code": "STT_001"
                # Note: Do NOT log the actual error message if it might contain PII
            },
            description="Transcription failed"
        )


# Example 7: Querying audit logs
def example_querying_audit_logs(db: Session):
    """Example of querying audit logs for compliance reporting"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    # Query all data access events for a user
    access_logs = audit_logger.query_audit_logs(
        event_type="data_access",
        actor_id=user_id,
        limit=100
    )
    
    print(f"Found {len(access_logs)} data access events for user")
    
    # Query all authentication attempts in the last 24 hours
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    auth_logs = audit_logger.query_audit_logs(
        event_type="authentication",
        start_date=yesterday,
        limit=1000
    )
    
    print(f"Found {len(auth_logs)} authentication attempts in last 24 hours")
    
    # Query all data deletion events
    deletion_logs = audit_logger.query_audit_logs(
        event_type="data_deletion",
        limit=100
    )
    
    print(f"Found {len(deletion_logs)} data deletion events")
    
    # Generate compliance report
    for log in deletion_logs:
        print(f"Deletion: {log.resource_type} at {log.timestamp}")
        print(f"  Result: {log.result}")
        print(f"  Metadata: {log.metadata}")


# Example 8: Integration with API endpoints
def example_api_endpoint_integration(db: Session, request):
    """
    Example of integrating audit logging into API endpoints
    
    This shows how to extract request information and log it
    """
    audit_logger = AuditLogger(db)
    
    # Extract information from request
    user_id = request.state.user_id  # From authentication middleware
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # Log the API access
    audit_logger.log_data_access(
        resource_type="api_endpoint",
        actor_id=user_id,
        action="request",
        result="success",
        metadata={
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": 200
        },
        description=f"{request.method} request to {request.url.path}",
        ip_address=ip_address,
        user_agent=user_agent
    )


# Example 9: Batch logging for bulk operations
def example_batch_logging(db: Session):
    """Example of logging bulk operations"""
    audit_logger = AuditLogger(db)
    
    admin_id = uuid4()
    
    # Log bulk data processing
    audit_logger.log_data_processing(
        operation="bulk_anonymization",
        resource_type="transaction",
        actor_id=admin_id,
        result="success",
        metadata={
            "record_count": 500,
            "operation_duration_ms": 5000,
            "anonymization_method": "hash_based"
        },
        description="Bulk anonymization of transactions for third-party sharing"
    )


# Example 10: Verifying PII compliance
def example_pii_verification(db: Session):
    """Example of verifying that logs don't contain PII"""
    audit_logger = AuditLogger(db)
    
    user_id = uuid4()
    
    # Create a log
    audit_log = audit_logger.log_data_access(
        resource_type="user",
        actor_id=user_id,
        action="read",
        result="success",
        metadata={
            "operation": "profile_view",
            "record_count": 1
        }
    )
    
    # Verify no PII
    is_compliant = audit_logger.verify_no_pii_in_logs(audit_log)
    
    if is_compliant:
        print("✓ Audit log is PII-compliant")
    else:
        print("✗ WARNING: Audit log contains PII!")


if __name__ == "__main__":
    print("Audit Logging Usage Examples")
    print("=" * 50)
    print()
    print("This file demonstrates how to use the AuditLogger service")
    print("to log various operations while maintaining PII compliance.")
    print()
    print("Key features:")
    print("- All user and resource IDs are hashed")
    print("- IP addresses are anonymized")
    print("- PII is automatically removed from metadata")
    print("- Comprehensive querying capabilities")
    print("- Support for all major operation types")
