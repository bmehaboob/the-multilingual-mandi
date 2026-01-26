"""User model"""
from sqlalchemy import Column, String, DateTime, Boolean, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class User(Base):
    """User model for farmers and traders"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    primary_language = Column(String(10), nullable=False)
    secondary_languages = Column(ARRAY(String), default=[])
    location = Column(JSONB, nullable=True)
    voiceprint_id = Column(UUID(as_uuid=True), nullable=True)  # Kept for backward compatibility
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    preferences = Column(JSONB, default={})  # Kept for backward compatibility
    
    # Relationships
    user_preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    voiceprint = relationship("Voiceprint", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.name} ({self.phone_number})>"
