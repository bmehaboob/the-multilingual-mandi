"""Transaction management service"""
import logging
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models.transaction import Transaction
from app.models.user import User
from app.models.conversation import Conversation
from app.services.audit.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for managing transactions and transaction history"""
    
    HISTORY_RETENTION_DAYS = 90
    DEFAULT_HISTORY_LIMIT = 5
    
    def create_transaction(
        self,
        db: Session,
        buyer_id: str,
        seller_id: str,
        commodity: str,
        quantity: float,
        unit: str,
        agreed_price: float,
        market_average_at_time: Optional[float] = None,
        conversation_id: Optional[str] = None,
        location: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Transaction], Optional[str]]:
        """
        Create a new transaction record.
        
        Requirements: 13.1, 15.10
        
        Args:
            db: Database session
            buyer_id: Buyer user ID
            seller_id: Seller user ID
            commodity: Commodity name
            quantity: Quantity traded
            unit: Unit of measurement
            agreed_price: Final agreed price
            market_average_at_time: Market average price at transaction time
            conversation_id: Optional conversation ID
            location: Optional location data
            ip_address: Optional IP address for audit logging
            user_agent: Optional user agent for audit logging
        
        Returns:
            Tuple of (success, transaction, error_message)
        """
        try:
            # Validate user IDs
            try:
                buyer_uuid = UUID(buyer_id)
                seller_uuid = UUID(seller_id)
            except ValueError as e:
                return False, None, f"Invalid UUID format: {str(e)}"
            
            # Verify both users exist
            buyer = db.query(User).filter(User.id == buyer_uuid).first()
            seller = db.query(User).filter(User.id == seller_uuid).first()
            
            if not buyer:
                return False, None, f"Buyer not found: {buyer_id}"
            if not seller:
                return False, None, f"Seller not found: {seller_id}"
            
            # Validate conversation if provided
            conversation_uuid = None
            if conversation_id:
                try:
                    conversation_uuid = UUID(conversation_id)
                    conversation = db.query(Conversation).filter(
                        Conversation.id == conversation_uuid
                    ).first()
                    if not conversation:
                        return False, None, f"Conversation not found: {conversation_id}"
                except ValueError:
                    return False, None, f"Invalid conversation UUID: {conversation_id}"
            
            # Validate transaction data
            if quantity <= 0:
                return False, None, "Quantity must be positive"
            if agreed_price < 0:
                return False, None, "Agreed price cannot be negative"
            if market_average_at_time is not None and market_average_at_time < 0:
                return False, None, "Market average cannot be negative"
            
            # Create transaction
            transaction = Transaction(
                buyer_id=buyer_uuid,
                seller_id=seller_uuid,
                commodity=commodity,
                quantity=quantity,
                unit=unit,
                agreed_price=agreed_price,
                market_average_at_time=market_average_at_time,
                conversation_id=conversation_uuid,
                completed_at=datetime.utcnow(),
                location=location
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(
                f"Created transaction {transaction.id}: "
                f"{buyer_id} bought {quantity} {unit} of {commodity} "
                f"from {seller_id} at {agreed_price}"
            )
            
            # Audit logging
            audit_logger = AuditLogger(db)
            audit_logger.log_data_access(
                resource_type="transaction",
                resource_id=transaction.id,
                actor_id=buyer_uuid,
                action="create",
                result="success",
                metadata={
                    "commodity": commodity,
                    "quantity": quantity,
                    "unit": unit,
                    "agreed_price": agreed_price,
                    "has_market_average": market_average_at_time is not None
                },
                description=f"Transaction created for {commodity}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, transaction, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating transaction: {str(e)}")
            return False, None, f"Failed to create transaction: {str(e)}"
    
    def get_transaction(
        self,
        db: Session,
        transaction_id: str,
        user_id: str
    ) -> Tuple[bool, Optional[Transaction], Optional[str]]:
        """
        Get a specific transaction.
        
        Requirements: 13.2
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            user_id: User ID (to verify access)
        
        Returns:
            Tuple of (success, transaction, error_message)
        """
        try:
            # Validate IDs
            try:
                txn_uuid = UUID(transaction_id)
                user_uuid = UUID(user_id)
            except ValueError as e:
                return False, None, f"Invalid UUID format: {str(e)}"
            
            # Get transaction
            transaction = db.query(Transaction).filter(
                Transaction.id == txn_uuid
            ).first()
            
            if not transaction:
                return False, None, f"Transaction not found: {transaction_id}"
            
            # Verify user is buyer or seller
            if transaction.buyer_id != user_uuid and transaction.seller_id != user_uuid:
                return False, None, "User is not a party to this transaction"
            
            return True, transaction, None
            
        except Exception as e:
            logger.error(f"Error retrieving transaction: {str(e)}")
            return False, None, f"Failed to retrieve transaction: {str(e)}"
    
    def get_user_transaction_history(
        self,
        db: Session,
        user_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        commodity_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, List[Transaction], int, Optional[str]]:
        """
        Get transaction history for a user.
        
        Requirements: 13.2, 13.3, 13.4, 15.10
        
        Args:
            db: Database session
            user_id: User ID
            limit: Optional limit on number of transactions
            offset: Offset for pagination
            commodity_filter: Optional commodity filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            ip_address: Optional IP address for audit logging
            user_agent: Optional user agent for audit logging
        
        Returns:
            Tuple of (success, transactions, total_count, error_message)
        """
        try:
            # Validate user ID
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                return False, [], 0, f"Invalid UUID format: {user_id}"
            
            # Verify user exists
            user = db.query(User).filter(User.id == user_uuid).first()
            if not user:
                return False, [], 0, f"User not found: {user_id}"
            
            # Build base query - transactions where user is buyer or seller
            query = db.query(Transaction).filter(
                or_(
                    Transaction.buyer_id == user_uuid,
                    Transaction.seller_id == user_uuid
                )
            )
            
            # Apply commodity filter
            if commodity_filter:
                query = query.filter(Transaction.commodity == commodity_filter)
            
            # Apply date filters
            if start_date:
                query = query.filter(Transaction.completed_at >= start_date)
            if end_date:
                query = query.filter(Transaction.completed_at <= end_date)
            
            # Apply retention policy - only return transactions within retention period
            retention_cutoff = datetime.utcnow() - timedelta(days=self.HISTORY_RETENTION_DAYS)
            query = query.filter(Transaction.completed_at >= retention_cutoff)
            
            # Get total count
            total_count = query.count()
            
            # Order by most recent first
            query = query.order_by(desc(Transaction.completed_at))
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            transactions = query.all()
            
            logger.info(
                f"Retrieved {len(transactions)} transactions for user {user_id} "
                f"(total: {total_count})"
            )
            
            # Audit logging
            audit_logger = AuditLogger(db)
            audit_logger.log_data_access(
                resource_type="transaction",
                resource_id=None,  # Multiple transactions accessed
                actor_id=user_uuid,
                action="list",
                result="success",
                metadata={
                    "record_count": len(transactions),
                    "total_count": total_count,
                    "has_commodity_filter": commodity_filter is not None,
                    "has_date_filter": start_date is not None or end_date is not None
                },
                description=f"User accessed transaction history ({len(transactions)} records)",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, transactions, total_count, None
            
        except Exception as e:
            logger.error(f"Error retrieving transaction history: {str(e)}")
            return False, [], 0, f"Failed to retrieve transaction history: {str(e)}"
    
    def get_recent_transactions(
        self,
        db: Session,
        user_id: str,
        limit: int = DEFAULT_HISTORY_LIMIT
    ) -> Tuple[bool, List[Transaction], Optional[str]]:
        """
        Get recent transactions for voice playback.
        
        Requirements: 13.3
        
        Args:
            db: Database session
            user_id: User ID
            limit: Number of recent transactions to retrieve (default: 5)
        
        Returns:
            Tuple of (success, transactions, error_message)
        """
        success, transactions, total_count, error = self.get_user_transaction_history(
            db=db,
            user_id=user_id,
            limit=limit,
            offset=0
        )
        
        return success, transactions, error
    
    def format_transaction_for_voice(
        self,
        transaction: Transaction,
        user_id: str,
        language: str = "en"
    ) -> str:
        """
        Format a transaction for voice playback.
        
        Requirements: 13.3
        
        Args:
            transaction: Transaction object
            user_id: Current user ID (to determine perspective)
            language: Language code for formatting
        
        Returns:
            Formatted string for voice output
        """
        try:
            user_uuid = UUID(user_id)
            
            # Determine user's role in transaction
            if transaction.buyer_id == user_uuid:
                role = "bought"
                other_party = "seller"
            elif transaction.seller_id == user_uuid:
                role = "sold"
                other_party = "buyer"
            else:
                role = "involved in"
                other_party = "other party"
            
            # Format date
            date_str = transaction.completed_at.strftime("%B %d, %Y")
            
            # Build voice message
            message = (
                f"On {date_str}, you {role} "
                f"{transaction.quantity} {transaction.unit} of {transaction.commodity} "
                f"at {transaction.agreed_price} rupees per {transaction.unit}."
            )
            
            # Add market comparison if available
            if transaction.market_average_at_time:
                diff_percent = (
                    (transaction.agreed_price - transaction.market_average_at_time) 
                    / transaction.market_average_at_time * 100
                )
                if abs(diff_percent) > 5:
                    if diff_percent > 0:
                        message += f" This was {abs(diff_percent):.1f}% above market average."
                    else:
                        message += f" This was {abs(diff_percent):.1f}% below market average."
                else:
                    message += " This was at market average."
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting transaction for voice: {str(e)}")
            return "Transaction details unavailable."
    
    def get_transaction_history_for_voice(
        self,
        db: Session,
        user_id: str,
        language: str = "en",
        limit: int = DEFAULT_HISTORY_LIMIT
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Get formatted transaction history for voice playback.
        
        Requirements: 13.3
        
        Args:
            db: Database session
            user_id: User ID
            language: Language code for formatting
            limit: Number of transactions to retrieve
        
        Returns:
            Tuple of (success, formatted_messages, error_message)
        """
        # Get recent transactions
        success, transactions, error = self.get_recent_transactions(
            db=db,
            user_id=user_id,
            limit=limit
        )
        
        if not success:
            return False, [], error
        
        if not transactions:
            return True, ["You have no recent transactions."], None
        
        # Format each transaction for voice
        formatted_messages = []
        for i, transaction in enumerate(transactions, 1):
            message = f"Transaction {i}. " + self.format_transaction_for_voice(
                transaction, user_id, language
            )
            formatted_messages.append(message)
        
        return True, formatted_messages, None
    
    def get_transactions_between_users(
        self,
        db: Session,
        user1_id: str,
        user2_id: str,
        limit: Optional[int] = None
    ) -> Tuple[bool, List[Transaction], Optional[str]]:
        """
        Get all transactions between two users.
        
        Useful for relationship analysis in negotiation context.
        
        Args:
            db: Database session
            user1_id: First user ID
            user2_id: Second user ID
            limit: Optional limit on number of transactions
        
        Returns:
            Tuple of (success, transactions, error_message)
        """
        try:
            # Validate user IDs
            try:
                user1_uuid = UUID(user1_id)
                user2_uuid = UUID(user2_id)
            except ValueError as e:
                return False, [], f"Invalid UUID format: {str(e)}"
            
            # Query transactions where users are buyer/seller in either direction
            query = db.query(Transaction).filter(
                or_(
                    and_(
                        Transaction.buyer_id == user1_uuid,
                        Transaction.seller_id == user2_uuid
                    ),
                    and_(
                        Transaction.buyer_id == user2_uuid,
                        Transaction.seller_id == user1_uuid
                    )
                )
            )
            
            # Apply retention policy
            retention_cutoff = datetime.utcnow() - timedelta(days=self.HISTORY_RETENTION_DAYS)
            query = query.filter(Transaction.completed_at >= retention_cutoff)
            
            # Order by most recent first
            query = query.order_by(desc(Transaction.completed_at))
            
            # Apply limit if provided
            if limit:
                query = query.limit(limit)
            
            transactions = query.all()
            
            logger.info(
                f"Retrieved {len(transactions)} transactions between "
                f"users {user1_id} and {user2_id}"
            )
            return True, transactions, None
            
        except Exception as e:
            logger.error(f"Error retrieving transactions between users: {str(e)}")
            return False, [], f"Failed to retrieve transactions: {str(e)}"
    
    def get_transaction_statistics(
        self,
        db: Session,
        user_id: str,
        commodity: Optional[str] = None,
        days: int = 30
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        Get transaction statistics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            commodity: Optional commodity filter
            days: Number of days to look back
        
        Returns:
            Tuple of (success, statistics_dict, error_message)
        """
        try:
            # Validate user ID
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                return False, {}, f"Invalid UUID format: {user_id}"
            
            # Calculate date range
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get transactions
            success, transactions, total_count, error = self.get_user_transaction_history(
                db=db,
                user_id=user_id,
                commodity_filter=commodity,
                start_date=start_date
            )
            
            if not success:
                return False, {}, error
            
            # Calculate statistics
            stats = {
                "total_transactions": len(transactions),
                "total_as_buyer": sum(1 for t in transactions if t.buyer_id == user_uuid),
                "total_as_seller": sum(1 for t in transactions if t.seller_id == user_uuid),
                "commodities_traded": len(set(t.commodity for t in transactions)),
                "total_value_as_buyer": sum(
                    t.agreed_price * t.quantity 
                    for t in transactions if t.buyer_id == user_uuid
                ),
                "total_value_as_seller": sum(
                    t.agreed_price * t.quantity 
                    for t in transactions if t.seller_id == user_uuid
                ),
                "period_days": days
            }
            
            return True, stats, None
            
        except Exception as e:
            logger.error(f"Error calculating transaction statistics: {str(e)}")
            return False, {}, f"Failed to calculate statistics: {str(e)}"
