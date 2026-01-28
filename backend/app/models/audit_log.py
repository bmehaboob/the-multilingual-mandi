"""
Audit Log Model

Stores audit logs of all data access and processing activities for compliance
verification as required by DPDP Act.

Requirements: 15.10 - Audit log maintenance for compliance
Property 54: Audit Log Maintenance
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.core.database import Base


class AuditLog(Base):
    """
    Audit log model for tracking data access and processing operations.
    
    This model stores audit events for compliance verification without
    containing any personally identifiable information (PII).
    
    All user identifiers are anonymized (hashed) to protect privacy while
    maintaining audit trail for compliance purposes.
    
    Requirements: 15.10
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp of the event
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Event type (e.g., "data_access", "data_processing", "data_export", "data_deletion")
    event_type = Column(String(100), nullable=False, index=True)
    
    # Event category (e.g., "user_data", "transaction", "conversation", "price_data")
    event_category = Column(String(100), nullable=False, index=True)
    
    # Action performed (e.g., "read", "write", "update", "delete", "export")
    action = Column(String(50), nullable=False, index=True)
    
    # Resource type (e.g., "user", "transaction", "message", "voiceprint")
    resource_type = Column(String(100), nullable=False)
    
    # Anonymized resource ID (hashed to prevent PII exposure)
    resource_id_hash = Column(String(64), nullable=True, index=True)
    
    # Anonymized user ID who performed the action (hashed)
    actor_id_hash = Column(String(64), nullable=True, index=True)
    
    # Result of the operation (e.g., "success", "failure", "partial")
    result = Column(String(50), nullable=False)
    
    # Additional metadata (must not contain PII)
    # Examples: record_count, operation_duration_ms, error_code
    event_metadata = Column("metadata", JSONB, default={})
    
    # Human-readable description of the event
    description = Column(Text, nullable=True)
    
    # IP address (anonymized - only first 3 octets for IPv4, first 48 bits for IPv6)
    ip_address_anonymized = Column(String(50), nullable=True)
    
    # User agent (browser/client information)
    user_agent = Column(String(500), nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_timestamp_event_type', 'timestamp', 'event_type'),
        Index('idx_audit_actor_timestamp', 'actor_id_hash', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id_hash'),
    )
    
    def __repr__(self):
        return (
            f"<AuditLog {self.event_type}/{self.action} "
            f"on {self.resource_type} at {self.timestamp}>"
        )
