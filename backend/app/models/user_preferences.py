"""User preferences model"""
from sqlalchemy import Column, String, Boolean, Float, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class UserPreferences(Base):
    """User preferences for speech and UI settings"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Speech settings
    speech_rate = Column(Float, default=0.85, nullable=False)  # 0.8-1.2 range, default 15% slower
    volume_boost = Column(Boolean, default=False, nullable=False)
    
    # Mode settings
    offline_mode = Column(Boolean, default=False, nullable=False)
    
    # Favorite contacts
    favorite_contacts = Column(ARRAY(UUID), default=[], nullable=False)
    
    # Additional preferences stored as JSON for flexibility
    additional_settings = Column(JSONB, default={}, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="user_preferences")
    
    def __repr__(self):
        return f"<UserPreferences for user {self.user_id}>"
