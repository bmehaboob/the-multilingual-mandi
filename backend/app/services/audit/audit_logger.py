"""
Audit Logging Service

Provides comprehensive audit logging for all data access and processing
operations while ensuring no PII is logged.

Requirements: 15.10 - Audit log maintenance for compliance
Property 54: Audit Log Maintenance
Property 45: Privacy-Preserving Error Logging
"""
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Service for logging data access and processing operations.
    
    This service creates audit logs for compliance verification while
    ensuring that no personally identifiable information (PII) is stored
    in the logs.
    
    All user and resource identifiers are hashed before storage to maintain
    privacy while preserving audit trail integrity.
    
    Requirements: 15.10
    """
    
    # Salt for hashing identifiers (should be stored securely in production)
    HASH_SALT = "multilingual-mandi-audit-salt-v1"
    
    # PII fields that should never be logged
    PII_FIELDS = {
        "name", "phone_number", "phone", "email", "address",
        "voiceprint", "voiceprint_data", "audio", "audio_data",
        "latitude", "longitude", "coordinates", "gps",
        "street", "house_number", "postal_code", "zip_code",
        "password", "pin", "secret", "token", "api_key"
    }
    
    def __init__(self, db: Session):
        """
        Initialize the audit logger.
        
        Args:
            db: Database session for storing audit logs
        """
        self.db = db
    
    def _hash_identifier(self, identifier: Any) -> str:
        """
        Create a one-way hash of an identifier.
        
        This allows tracking operations on the same resource without
        exposing the actual identifier.
        
        Args:
            identifier: The identifier to hash (UUID, string, etc.)
            
        Returns:
            A hexadecimal hash string
        """
        # Convert to string and combine with salt
        data = f"{str(identifier)}{self.HASH_SALT}"
        # Use SHA-256 for one-way hashing
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _anonymize_ip_address(self, ip_address: Optional[str]) -> Optional[str]:
        """
        Anonymize an IP address by removing the last octet(s).
        
        For IPv4: Keep first 3 octets (e.g., 192.168.1.x)
        For IPv6: Keep first 48 bits
        
        Args:
            ip_address: The IP address to anonymize
            
        Returns:
            Anonymized IP address or None
        """
        if not ip_address:
            return None
        
        # Simple IPv4 anonymization
        if '.' in ip_address:
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.x"
        
        # Simple IPv6 anonymization
        if ':' in ip_address:
            parts = ip_address.split(':')
            if len(parts) >= 3:
                return ':'.join(parts[:3]) + ':x:x:x:x:x'
        
        return "anonymized"
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove any PII from metadata before logging.
        
        Args:
            metadata: Dictionary that may contain various fields
            
        Returns:
            Sanitized metadata without PII
        """
        if not metadata:
            return {}
        
        sanitized = {}
        for key, value in metadata.items():
            # Skip PII fields
            if key.lower() in self.PII_FIELDS:
                sanitized[key] = "[REDACTED]"
                continue
            
            # Recursively sanitize nested dictionaries
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_metadata(value)
            # Sanitize lists
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_metadata(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_data_access(
        self,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: str = "read",
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a data access operation.
        
        Args:
            resource_type: Type of resource accessed (e.g., "user", "transaction")
            resource_id: UUID of the resource (will be hashed)
            actor_id: UUID of the user performing the action (will be hashed)
            action: Action performed (e.g., "read", "list", "search")
            result: Result of the operation (e.g., "success", "failure")
            metadata: Additional metadata (will be sanitized)
            description: Human-readable description
            ip_address: IP address of the request (will be anonymized)
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
            
        Requirements: 15.10
        """
        # Sanitize metadata to remove PII
        sanitized_metadata = self._sanitize_metadata(metadata or {})
        
        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type="data_access",
            event_category=resource_type,
            action=action,
            resource_type=resource_type,
            resource_id_hash=self._hash_identifier(resource_id) if resource_id else None,
            actor_id_hash=self._hash_identifier(actor_id) if actor_id else None,
            result=result,
            event_metadata=sanitized_metadata,
            description=description,
            ip_address_anonymized=self._anonymize_ip_address(ip_address),
            user_agent=user_agent[:500] if user_agent else None  # Truncate long user agents
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(
            f"Audit log created: {audit_log.event_type}/{audit_log.action} "
            f"on {audit_log.resource_type} - {audit_log.result}"
        )
        
        return audit_log
    
    def log_data_processing(
        self,
        operation: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a data processing operation.
        
        Examples: transcription, translation, voice synthesis, price calculation
        
        Args:
            operation: Type of processing (e.g., "transcription", "translation")
            resource_type: Type of resource being processed
            resource_id: UUID of the resource (will be hashed)
            actor_id: UUID of the user (will be hashed)
            result: Result of the operation
            metadata: Additional metadata (will be sanitized)
            description: Human-readable description
            ip_address: IP address (will be anonymized)
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
            
        Requirements: 15.10
        """
        # Sanitize metadata to remove PII
        sanitized_metadata = self._sanitize_metadata(metadata or {})
        
        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type="data_processing",
            event_category=operation,
            action="process",
            resource_type=resource_type,
            resource_id_hash=self._hash_identifier(resource_id) if resource_id else None,
            actor_id_hash=self._hash_identifier(actor_id) if actor_id else None,
            result=result,
            event_metadata=sanitized_metadata,
            description=description,
            ip_address_anonymized=self._anonymize_ip_address(ip_address),
            user_agent=user_agent[:500] if user_agent else None
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(
            f"Audit log created: {audit_log.event_type}/{operation} "
            f"on {audit_log.resource_type} - {audit_log.result}"
        )
        
        return audit_log
    
    def log_data_export(
        self,
        resource_type: str,
        actor_id: Optional[UUID] = None,
        record_count: int = 0,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a data export operation.
        
        Args:
            resource_type: Type of resource exported
            actor_id: UUID of the user (will be hashed)
            record_count: Number of records exported
            result: Result of the operation
            metadata: Additional metadata (will be sanitized)
            description: Human-readable description
            ip_address: IP address (will be anonymized)
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
            
        Requirements: 15.10
        """
        # Add record count to metadata
        export_metadata = metadata or {}
        export_metadata["record_count"] = record_count
        
        # Sanitize metadata
        sanitized_metadata = self._sanitize_metadata(export_metadata)
        
        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type="data_export",
            event_category=resource_type,
            action="export",
            resource_type=resource_type,
            resource_id_hash=None,  # Export operations don't have a single resource ID
            actor_id_hash=self._hash_identifier(actor_id) if actor_id else None,
            result=result,
            event_metadata=sanitized_metadata,
            description=description,
            ip_address_anonymized=self._anonymize_ip_address(ip_address),
            user_agent=user_agent[:500] if user_agent else None
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(
            f"Audit log created: {audit_log.event_type} "
            f"of {record_count} {audit_log.resource_type} records - {audit_log.result}"
        )
        
        return audit_log
    
    def log_data_deletion(
        self,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a data deletion operation.
        
        Args:
            resource_type: Type of resource deleted
            resource_id: UUID of the resource (will be hashed)
            actor_id: UUID of the user (will be hashed)
            result: Result of the operation
            metadata: Additional metadata (will be sanitized)
            description: Human-readable description
            ip_address: IP address (will be anonymized)
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
            
        Requirements: 15.10
        """
        # Sanitize metadata
        sanitized_metadata = self._sanitize_metadata(metadata or {})
        
        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type="data_deletion",
            event_category=resource_type,
            action="delete",
            resource_type=resource_type,
            resource_id_hash=self._hash_identifier(resource_id) if resource_id else None,
            actor_id_hash=self._hash_identifier(actor_id) if actor_id else None,
            result=result,
            event_metadata=sanitized_metadata,
            description=description,
            ip_address_anonymized=self._anonymize_ip_address(ip_address),
            user_agent=user_agent[:500] if user_agent else None
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(
            f"Audit log created: {audit_log.event_type} "
            f"of {audit_log.resource_type} - {audit_log.result}"
        )
        
        return audit_log
    
    def log_authentication(
        self,
        actor_id: Optional[UUID] = None,
        auth_method: str = "voice_biometric",
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an authentication attempt.
        
        Args:
            actor_id: UUID of the user (will be hashed)
            auth_method: Authentication method used
            result: Result of the authentication
            metadata: Additional metadata (will be sanitized)
            description: Human-readable description
            ip_address: IP address (will be anonymized)
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
            
        Requirements: 15.10
        """
        # Add auth method to metadata
        auth_metadata = metadata or {}
        auth_metadata["auth_method"] = auth_method
        
        # Sanitize metadata
        sanitized_metadata = self._sanitize_metadata(auth_metadata)
        
        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type="authentication",
            event_category="user_auth",
            action="authenticate",
            resource_type="user",
            resource_id_hash=None,
            actor_id_hash=self._hash_identifier(actor_id) if actor_id else None,
            result=result,
            event_metadata=sanitized_metadata,
            description=description,
            ip_address_anonymized=self._anonymize_ip_address(ip_address),
            user_agent=user_agent[:500] if user_agent else None
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(
            f"Audit log created: {audit_log.event_type} "
            f"via {auth_method} - {audit_log.result}"
        )
        
        return audit_log
    
    def query_audit_logs(
        self,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            event_type: Filter by event type
            resource_type: Filter by resource type
            actor_id: Filter by actor (will be hashed)
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            
        Returns:
            List of matching audit logs
        """
        query = self.db.query(AuditLog)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if actor_id:
            actor_hash = self._hash_identifier(actor_id)
            query = query.filter(AuditLog.actor_id_hash == actor_hash)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        return query.all()
    
    def verify_no_pii_in_logs(self, audit_log: AuditLog) -> bool:
        """
        Verify that an audit log contains no PII.
        
        This is a safety check to ensure compliance.
        
        Args:
            audit_log: The audit log to check
            
        Returns:
            True if no PII detected, False otherwise
        """
        # Check metadata for PII fields
        if audit_log.event_metadata:
            for key in audit_log.event_metadata.keys():
                if key.lower() in self.PII_FIELDS:
                    logger.error(
                        f"PII field '{key}' found in audit log {audit_log.id}"
                    )
                    return False
        
        # Check description for common PII patterns
        if audit_log.description:
            # Check for phone numbers (simple pattern)
            import re
            phone_pattern = r'\b\d{10,}\b'
            if re.search(phone_pattern, audit_log.description):
                logger.warning(
                    f"Potential phone number found in audit log {audit_log.id} description"
                )
                return False
        
        return True
