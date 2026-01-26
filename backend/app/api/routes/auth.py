"""Authentication API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    VoiceLoginRequest,
    PINLoginRequest,
    HybridLoginRequest,
    SetPINRequest,
    LoginResponse,
    LogoutResponse,
    SetPINResponse,
    TokenResponse,
    CurrentUserResponse
)
from app.services.auth.authentication_service import AuthenticationService
from app.api.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize authentication service
auth_service = AuthenticationService()


@router.post("/login/voice", response_model=LoginResponse)
async def login_with_voice(
    request: VoiceLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login using voice biometric authentication.
    
    Authenticates user by verifying their voice against stored voiceprint
    and returns a JWT access token for session management.
    
    Requirements: 21.2, 21.3
    
    Args:
        request: Voice login request with phone number and audio data
        db: Database session
    
    Returns:
        LoginResponse with JWT token if successful
    """
    logger.info(f"Voice login attempt for phone: {request.phone_number}")
    
    # Authenticate with voice
    success, user, error, confidence = auth_service.authenticate_with_voice(
        db=db,
        phone_number=request.phone_number,
        audio_data=request.audio_data,
        sample_rate=request.sample_rate
    )
    
    if not success:
        logger.warning(f"Voice login failed: {error}")
        return LoginResponse(
            success=False,
            message=error or "Voice authentication failed",
            token=None,
            verification_confidence=confidence,
            authentication_method="voice"
        )
    
    # Create session token
    access_token = auth_service.create_session_token(user)
    expires_in = auth_service.get_token_expiration_seconds()
    
    logger.info(f"Voice login successful for user {user.id}")
    
    return LoginResponse(
        success=True,
        message="Login successful",
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user_id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            primary_language=user.primary_language
        ),
        verification_confidence=confidence,
        authentication_method="voice"
    )


@router.post("/login/pin", response_model=LoginResponse)
async def login_with_pin(
    request: PINLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login using PIN-based authentication (fallback method).
    
    Authenticates user using their voice-based PIN as a fallback
    when voice biometric authentication is not available.
    
    Requirements: 21.4
    
    Args:
        request: PIN login request with phone number and PIN
        db: Database session
    
    Returns:
        LoginResponse with JWT token if successful
    """
    logger.info(f"PIN login attempt for phone: {request.phone_number}")
    
    # Authenticate with PIN
    success, user, error = auth_service.authenticate_with_pin(
        db=db,
        phone_number=request.phone_number,
        pin=request.pin
    )
    
    if not success:
        logger.warning(f"PIN login failed: {error}")
        return LoginResponse(
            success=False,
            message=error or "PIN authentication failed",
            token=None,
            verification_confidence=None,
            authentication_method="pin"
        )
    
    # Create session token
    access_token = auth_service.create_session_token(user)
    expires_in = auth_service.get_token_expiration_seconds()
    
    logger.info(f"PIN login successful for user {user.id}")
    
    return LoginResponse(
        success=True,
        message="Login successful",
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user_id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            primary_language=user.primary_language
        ),
        verification_confidence=1.0,
        authentication_method="pin"
    )


@router.post("/login/hybrid", response_model=LoginResponse)
async def login_hybrid(
    request: HybridLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with hybrid authentication (voice with PIN fallback).
    
    Attempts voice biometric authentication first, and falls back to
    PIN authentication if voice verification fails.
    
    Requirements: 21.2, 21.3, 21.4
    
    Args:
        request: Hybrid login request with phone number, optional audio, and optional PIN
        db: Database session
    
    Returns:
        LoginResponse with JWT token if successful
    """
    logger.info(f"Hybrid login attempt for phone: {request.phone_number}")
    
    # Authenticate with hybrid method
    success, user, error, confidence, method = auth_service.authenticate_hybrid(
        db=db,
        phone_number=request.phone_number,
        audio_data=request.audio_data,
        sample_rate=request.sample_rate,
        pin=request.pin
    )
    
    if not success:
        logger.warning(f"Hybrid login failed: {error}")
        return LoginResponse(
            success=False,
            message=error or "Authentication failed",
            token=None,
            verification_confidence=confidence if method == "voice" else None,
            authentication_method=method
        )
    
    # Create session token
    access_token = auth_service.create_session_token(user)
    expires_in = auth_service.get_token_expiration_seconds()
    
    logger.info(f"Hybrid login successful for user {user.id} using {method}")
    
    return LoginResponse(
        success=True,
        message=f"Login successful using {method}",
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user_id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            primary_language=user.primary_language
        ),
        verification_confidence=confidence if method == "voice" else None,
        authentication_method=method
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout the current user.
    
    Revokes the current session token. In production, this would add
    the token to a blacklist in Redis.
    
    Requirements: 21.2, 21.3
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        LogoutResponse confirming logout
    """
    logger.info(f"Logout for user {current_user.id}")
    
    # Revoke session (in production, add token to blacklist)
    auth_service.revoke_session("")  # Token would be extracted from request
    
    return LogoutResponse(
        success=True,
        message="Logout successful"
    )


@router.post("/pin/set", response_model=SetPINResponse)
async def set_pin(
    request: SetPINRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Set a PIN for fallback authentication.
    
    Allows authenticated users to set a voice-based PIN as a fallback
    authentication method when voice biometrics fail.
    
    Requirements: 21.4
    
    Args:
        request: Set PIN request with PIN value
        current_user: Current authenticated user
    
    Returns:
        SetPINResponse confirming PIN was set
    """
    logger.info(f"Setting PIN for user {current_user.id}")
    
    success, message = auth_service.set_user_pin(
        user_id=str(current_user.id),
        pin=request.pin
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SetPINResponse(
        success=True,
        message=message
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Returns information about the currently authenticated user based
    on the JWT token provided in the request.
    
    Requirements: 21.2, 21.3
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        CurrentUserResponse with user information
    """
    logger.info(f"Getting info for user {current_user.id}")
    
    return CurrentUserResponse(
        user_id=str(current_user.id),
        phone_number=current_user.phone_number,
        name=current_user.name,
        primary_language=current_user.primary_language,
        secondary_languages=current_user.secondary_languages or [],
        created_at=current_user.created_at,
        last_active=current_user.last_active
    )


@router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service.
    
    Returns:
        Status information about the authentication service
    """
    stats = auth_service.voice_verification.get_verification_stats()
    
    return {
        "status": "healthy",
        "service": "authentication",
        "voice_verification": {
            "enabled": True,
            "anti_spoofing": stats["anti_spoofing_enabled"],
            "threshold": stats["similarity_threshold"]
        }
    }
