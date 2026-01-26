"""Voiceprint model for voice biometric authentication"""
from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Voiceprint(Base):
    """Voiceprint model for storing voice biometric data"""
    __tablename__ = "voiceprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Encrypted voice embedding data
    # Stored as binary data (encrypted numpy array or similar)
    embedding_data = Column(LargeBinary, nullable=False)
    
    # Encryption metadata
    encryption_algorithm = Column(String(50), default="AES-256", nullable=False)
    
    # Number of samples used to create the voiceprint
    sample_count = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="voiceprint")
    
    def __repr__(self):
        return f"<Voiceprint for user {self.user_id}>"
