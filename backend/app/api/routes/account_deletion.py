"""
Account Deletion API Routes

Provides endpoints for managing account deletion requests in compliance
with DPDP Act requirements.

Requirements: 15.4 - Account deletion with data removal within 30 days
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.privacy.account_deletion_service import AccountDeletionService
from app.models.user import User


router = APIRouter(prefix="/account", tags=["account-deletion"])


# Request/Response Models
class AccountDeletionRequest(BaseModel):
    """Request model for account deletion"""
    reason: Optional[str] = Field(
        None,
        description="Optional reason for account deletion",
        max_length=500
    )


class AccountDeletionResponse(BaseModel):
    """Response model for account deletion request"""
    user_id: str
    deletion_requested_at: str
    deletion_scheduled_for: str
    grace_period_days: int
    status: str
    message: str


class DeletionStatusResponse(BaseModel):
    """Response model for deletion status"""
    user_id: str
    status: str
    deletion_requested: bool
    deletion_requested_at: Optional[str] = None
    deletion_scheduled_for: Optional[str] = None
    days_remaining: Optional[int] = None
    can_cancel: Optional[bool] = None
    reason: Optional[str] = None


class DeletionCancellationResponse(BaseModel):
    """Response model for deletion cancellation"""
    user_id: str
    status: str
    cancelled_at: str
    message: str


# Initialize service
deletion_service = AccountDeletionService()


@router.post(
    "/delete",
    response_model=AccountDeletionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request account deletion",
    description="""
    Request deletion of the authenticated user's account.
    
    The account will be marked for deletion and all personal data will be
    removed within 30 days as required by DPDP Act. The user can cancel
    the deletion request within this grace period.
    
    Immediately upon request:
    - Account access is disabled
    - Account is marked for deletion
    
    Within 30 days:
    - All personal data is permanently removed
    - Voiceprints are deleted
    - Messages are deleted
    - Transactions are anonymized
    
    Requirements: 15.4
    """
)
async def request_account_deletion(
    request: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AccountDeletionResponse:
    """
    Request account deletion for the authenticated user.
    
    Args:
        request: Deletion request with optional reason
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Deletion request confirmation with scheduled date
        
    Raises:
        HTTPException: If deletion request fails
    """
    try:
        result = deletion_service.request_account_deletion(
            db=db,
            user_id=str(current_user.id),
            reason=request.reason
        )
        
        return AccountDeletionResponse(
            **result,
            message=(
                f"Account deletion requested successfully. "
                f"Your account will be deleted on {result['deletion_scheduled_for']}. "
                f"You can cancel this request within {result['grace_period_days']} days."
            )
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request account deletion: {str(e)}"
        )


@router.get(
    "/deletion-status",
    response_model=DeletionStatusResponse,
    summary="Get account deletion status",
    description="""
    Get the current deletion status for the authenticated user's account.
    
    Returns information about:
    - Whether deletion has been requested
    - When deletion was requested
    - When deletion is scheduled
    - Days remaining until deletion
    - Whether cancellation is still possible
    
    Requirements: 15.4
    """
)
async def get_deletion_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DeletionStatusResponse:
    """
    Get deletion status for the authenticated user.
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Current deletion status
        
    Raises:
        HTTPException: If status check fails
    """
    try:
        status_info = deletion_service.get_deletion_status(
            db=db,
            user_id=str(current_user.id)
        )
        
        return DeletionStatusResponse(**status_info)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deletion status: {str(e)}"
        )


@router.post(
    "/cancel-deletion",
    response_model=DeletionCancellationResponse,
    summary="Cancel account deletion request",
    description="""
    Cancel a pending account deletion request.
    
    This can only be done within the 30-day grace period. After cancellation:
    - Account access is restored
    - Deletion markers are removed
    - Account returns to active status
    
    Requirements: 15.4
    """
)
async def cancel_deletion_request(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DeletionCancellationResponse:
    """
    Cancel account deletion for the authenticated user.
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Cancellation confirmation
        
    Raises:
        HTTPException: If cancellation fails
    """
    try:
        result = deletion_service.cancel_deletion_request(
            db=db,
            user_id=str(current_user.id)
        )
        
        return DeletionCancellationResponse(
            **result,
            message="Account deletion cancelled successfully. Your account is now active."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel deletion: {str(e)}"
        )


# Admin endpoint for executing scheduled deletions
@router.post(
    "/admin/execute-deletion/{user_id}",
    summary="Execute account deletion (Admin only)",
    description="""
    Execute account deletion for a specific user. This is typically called
    by scheduled jobs to process deletions after the grace period.
    
    This endpoint should be protected with admin authentication in production.
    
    Requirements: 15.4
    """,
    include_in_schema=False  # Hide from public API docs
)
async def execute_account_deletion(
    user_id: str,
    force: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute account deletion (admin endpoint).
    
    Args:
        user_id: UUID of the user to delete
        force: If True, bypass grace period check
        db: Database session
        
    Returns:
        Deletion summary
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        result = deletion_service.execute_account_deletion(
            db=db,
            user_id=user_id,
            force=force
        )
        
        return {
            **result,
            "message": "Account deleted successfully"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute deletion: {str(e)}"
        )


@router.get(
    "/admin/pending-deletions",
    summary="Get pending deletions (Admin only)",
    description="""
    Get list of accounts pending deletion. Used by scheduled jobs
    to process deletions.
    
    This endpoint should be protected with admin authentication in production.
    
    Requirements: 15.4
    """,
    include_in_schema=False  # Hide from public API docs
)
async def get_pending_deletions(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get pending deletions (admin endpoint).
    
    Args:
        db: Database session
        
    Returns:
        List of pending deletions
    """
    try:
        pending = deletion_service.get_pending_deletions(db=db)
        
        return {
            "count": len(pending),
            "pending_deletions": pending
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending deletions: {str(e)}"
        )
