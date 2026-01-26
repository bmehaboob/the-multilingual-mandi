"""Authentication schemas for API requests and responses"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class VoiceLoginRequest(BaseModel):
    """Request for voice biometric login"""
    phone_number: str = Field(..., description="User's phone number")
    audio_data: str = Field(..., description="Base64 encoded audio data")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not v or len(v) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v
    
    @validator('audio_data')
    def validate_audio_data(cls, v):
        """Validate audio data is not empty"""
        if not v:
            raise ValueError("Audio data is required")
        return v


class PINLoginRequest(BaseModel):
    """Request for PIN-based login (fallback)"""
    phone_number: str = Field(..., description="User's phone number")
    pin: str = Field(..., description="4-6 digit PIN")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not v or len(v) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v
    
    @validator('pin')
    def validate_pin(cls, v):
        """Validate PIN format"""
        if not v or not v.isdigit():
            raise ValueError("PIN must contain only digits")
        if len(v) < 4 or len(v) > 6:
            raise ValueError("PIN must be 4-6 digits")
        return v


class HybridLoginRequest(BaseModel):
    """Request for hybrid login (voice with PIN fallback)"""
    phone_number: str = Field(..., description="User's phone number")
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    pin: Optional[str] = Field(None, description="4-6 digit PIN (fallback)")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not v or len(v) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v
    
    @validator('pin')
    def validate_pin(cls, v):
        """Validate PIN format if provided"""
        if v is not None:
            if not v.isdigit():
                raise ValueError("PIN must contain only digits")
            if len(v) < 4 or len(v) > 6:
                raise ValueError("PIN must be 4-6 digits")
        return v


class SetPINRequest(BaseModel):
    """Request to set a PIN for fallback authentication"""
    pin: str = Field(..., description="4-6 digit PIN")
    
    @validator('pin')
    def validate_pin(cls, v):
        """Validate PIN format"""
        if not v or not v.isdigit():
            raise ValueError("PIN must contain only digits")
        if len(v) < 4 or len(v) > 6:
            raise ValueError("PIN must be 4-6 digits")
        return v


class TokenResponse(BaseModel):
    """Response containing access token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User ID")
    phone_number: str = Field(..., description="User's phone number")
    name: str = Field(..., description="User's name")
    primary_language: str = Field(..., description="User's primary language")


class LoginResponse(BaseModel):
    """Response for login attempts"""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Status message")
    token: Optional[TokenResponse] = Field(None, description="Token data if successful")
    verification_confidence: Optional[float] = Field(
        None,
        description="Voice verification confidence score (0.0-1.0)"
    )
    authentication_method: str = Field(
        ...,
        description="Method used for authentication (voice, pin, hybrid)"
    )


class LogoutResponse(BaseModel):
    """Response for logout"""
    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(..., description="Status message")


class SetPINResponse(BaseModel):
    """Response for setting PIN"""
    success: bool = Field(..., description="Whether PIN was set successfully")
    message: str = Field(..., description="Status message")


class CurrentUserResponse(BaseModel):
    """Response containing current user information"""
    user_id: str = Field(..., description="User ID")
    phone_number: str = Field(..., description="User's phone number")
    name: str = Field(..., description="User's name")
    primary_language: str = Field(..., description="User's primary language")
    secondary_languages: list[str] = Field(default=[], description="Secondary languages")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_active: datetime = Field(..., description="Last activity timestamp")
