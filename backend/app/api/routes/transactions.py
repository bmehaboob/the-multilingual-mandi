"""Transaction management API endpoints"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.transaction import (
    CreateTransactionRequest,
    TransactionResponse,
    TransactionHistoryResponse,
    VoiceTransactionHistoryResponse,
    TransactionStatisticsResponse,
    TransactionBetweenUsersResponse
)
from app.services.transaction_service import TransactionService
from app.api.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Initialize transaction service
transaction_service = TransactionService()


def _build_transaction_response(transaction, user_id: str = None) -> TransactionResponse:
    """Helper to build transaction response with computed fields"""
    total_value = transaction.agreed_price * transaction.quantity
    
    # Calculate price vs market
    price_vs_market = None
    if transaction.market_average_at_time:
        diff_percent = (
            (transaction.agreed_price - transaction.market_average_at_time) 
            / transaction.market_average_at_time * 100
        )
        if abs(diff_percent) <= 5:
            price_vs_market = "fair"
        elif diff_percent > 10:
            price_vs_market = "high"
        elif diff_percent < -10:
            price_vs_market = "low"
        else:
            price_vs_market = "fair"
    
    return TransactionResponse(
        id=str(transaction.id),
        buyer_id=str(transaction.buyer_id),
        seller_id=str(transaction.seller_id),
        commodity=transaction.commodity,
        quantity=transaction.quantity,
        unit=transaction.unit,
        agreed_price=transaction.agreed_price,
        market_average_at_time=transaction.market_average_at_time,
        conversation_id=str(transaction.conversation_id) if transaction.conversation_id else None,
        completed_at=transaction.completed_at,
        location=transaction.location,
        total_value=total_value,
        price_vs_market=price_vs_market
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction record.
    
    Records a completed transaction between a buyer and seller. The current user
    must be either the buyer or seller in the transaction.
    
    Requirements: 13.1
    
    Args:
        request: Transaction creation request
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        TransactionResponse with transaction details
    
    Raises:
        HTTPException: If validation fails or creation fails
    """
    logger.info(f"Creating transaction for user {current_user.id}")
    
    # Verify current user is buyer or seller
    if str(current_user.id) not in [request.buyer_id, request.seller_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user must be either buyer or seller"
        )
    
    # Create transaction
    success, transaction, error = transaction_service.create_transaction(
        db=db,
        buyer_id=request.buyer_id,
        seller_id=request.seller_id,
        commodity=request.commodity,
        quantity=request.quantity,
        unit=request.unit,
        agreed_price=request.agreed_price,
        market_average_at_time=request.market_average_at_time,
        conversation_id=request.conversation_id,
        location=request.location
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    logger.info(f"Created transaction {transaction.id}")
    
    return _build_transaction_response(transaction, str(current_user.id))


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific transaction.
    
    Returns details of a transaction. The current user must be either the buyer
    or seller in the transaction.
    
    Requirements: 13.2
    
    Args:
        transaction_id: Transaction ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        TransactionResponse with transaction details
    
    Raises:
        HTTPException: If transaction not found or user not authorized
    """
    logger.info(f"Getting transaction {transaction_id} for user {current_user.id}")
    
    # Get transaction
    success, transaction, error = transaction_service.get_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        elif "not a party" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    return _build_transaction_response(transaction, str(current_user.id))


@router.get("", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    limit: Optional[int] = Query(None, description="Maximum number of transactions", ge=1, le=100),
    offset: int = Query(0, description="Number of transactions to skip", ge=0),
    commodity: Optional[str] = Query(None, description="Filter by commodity"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for the current user.
    
    Returns all transactions where the current user is either buyer or seller,
    ordered by most recent first. Supports filtering and pagination.
    Transactions are retained for 90 days.
    
    Requirements: 13.2, 13.4
    
    Args:
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip
        commodity: Optional commodity filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        TransactionHistoryResponse with list of transactions
    
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(f"Getting transaction history for user {current_user.id}")
    
    # Get transaction history
    success, transactions, total_count, error = transaction_service.get_user_transaction_history(
        db=db,
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
        commodity_filter=commodity,
        start_date=start_date,
        end_date=end_date
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Build response
    transaction_responses = [
        _build_transaction_response(txn, str(current_user.id))
        for txn in transactions
    ]
    
    logger.info(f"Retrieved {len(transactions)} transactions for user {current_user.id}")
    
    return TransactionHistoryResponse(
        transactions=transaction_responses,
        total=total_count,
        limit=limit,
        offset=offset
    )


@router.get("/voice/history", response_model=VoiceTransactionHistoryResponse)
async def get_voice_transaction_history(
    language: str = Query("en", description="Language code for voice output"),
    limit: int = Query(5, description="Number of recent transactions", ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get formatted transaction history for voice playback.
    
    Returns the most recent transactions formatted as natural language messages
    suitable for text-to-speech output. By default returns the last 5 transactions.
    
    Requirements: 13.3
    
    Args:
        language: Language code for formatting (default: en)
        limit: Number of recent transactions (default: 5, max: 10)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        VoiceTransactionHistoryResponse with formatted messages
    
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(
        f"Getting voice transaction history for user {current_user.id} "
        f"in language {language}"
    )
    
    # Get formatted transaction history
    success, messages, error = transaction_service.get_transaction_history_for_voice(
        db=db,
        user_id=str(current_user.id),
        language=language,
        limit=limit
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    logger.info(
        f"Retrieved {len(messages)} formatted messages for user {current_user.id}"
    )
    
    return VoiceTransactionHistoryResponse(
        messages=messages,
        transaction_count=len(messages) if messages[0] != "You have no recent transactions." else 0,
        language=language
    )


@router.get("/statistics/summary", response_model=TransactionStatisticsResponse)
async def get_transaction_statistics(
    commodity: Optional[str] = Query(None, description="Filter by commodity"),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction statistics for the current user.
    
    Returns aggregated statistics about the user's transactions over a specified
    time period, including counts, values, and commodity diversity.
    
    Args:
        commodity: Optional commodity filter
        days: Number of days to look back (default: 30)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        TransactionStatisticsResponse with statistics
    
    Raises:
        HTTPException: If calculation fails
    """
    logger.info(f"Getting transaction statistics for user {current_user.id}")
    
    # Get statistics
    success, stats, error = transaction_service.get_transaction_statistics(
        db=db,
        user_id=str(current_user.id),
        commodity=commodity,
        days=days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return TransactionStatisticsResponse(**stats)


@router.get("/between/{other_user_id}", response_model=TransactionBetweenUsersResponse)
async def get_transactions_between_users(
    other_user_id: str,
    limit: Optional[int] = Query(None, description="Maximum number of transactions", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all transactions between current user and another user.
    
    Returns all transactions where the current user and the specified user
    are buyer and seller (in either direction). Useful for viewing trading
    history with a specific partner.
    
    Args:
        other_user_id: Other user ID
        limit: Optional limit on number of transactions
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        TransactionBetweenUsersResponse with list of transactions
    
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(
        f"Getting transactions between users {current_user.id} and {other_user_id}"
    )
    
    # Get transactions
    success, transactions, error = transaction_service.get_transactions_between_users(
        db=db,
        user1_id=str(current_user.id),
        user2_id=other_user_id,
        limit=limit
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Build response
    transaction_responses = [
        _build_transaction_response(txn, str(current_user.id))
        for txn in transactions
    ]
    
    logger.info(
        f"Retrieved {len(transactions)} transactions between "
        f"users {current_user.id} and {other_user_id}"
    )
    
    return TransactionBetweenUsersResponse(
        user1_id=str(current_user.id),
        user2_id=other_user_id,
        transactions=transaction_responses,
        total=len(transactions)
    )


@router.get("/health")
async def transaction_health_check():
    """
    Health check endpoint for transaction service.
    
    Returns:
        Status information about the transaction service
    """
    return {
        "status": "healthy",
        "service": "transactions",
        "retention_days": TransactionService.HISTORY_RETENTION_DAYS,
        "default_history_limit": TransactionService.DEFAULT_HISTORY_LIMIT
    }
