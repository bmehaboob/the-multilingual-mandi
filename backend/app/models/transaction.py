"""Transaction model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.core.database import Base


class Transaction(Base):
    """Transaction model for completed trades"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    commodity = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    agreed_price = Column(Float, nullable=False)
    market_average_at_time = Column(Float, nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    location = Column(JSONB, nullable=True)
    
    def __repr__(self):
        return f"<Transaction {self.id} - {self.commodity}>"
