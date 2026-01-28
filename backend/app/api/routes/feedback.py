"""
API routes for feedback collection.

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.feedback import (
    TranscriptionFeedback,
    NegotiationFeedback,
    SatisfactionSurvey,
    TranslationFeedback,
    PriceOracleFeedback
)
from app.models.user import User
from app.schemas.feedback import (
    TranscriptionCorrectionCreate,
    TranscriptionCorrectionResponse,
    NegotiationFeedbackCreate,
    NegotiationFeedbackResponse,
    SatisfactionSurveyCreate,
    SatisfactionSurveyResponse,
    TranslationFeedbackCreate,
    TranslationFeedbackResponse,
    PriceOracleFeedbackCreate,
    PriceOracleFeedbackResponse,
    VoiceSurveyRequest,
    VoiceSurveyPrompt
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "/transcription-correction",
    response_model=TranscriptionCorrectionResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_transcription_correction(
    correction: TranscriptionCorrectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a transcription correction for model improvement.
    
    Requirements: 20.1
    
    This endpoint allows users to correct transcription errors, which are logged
    for future model training and improvement.
    """
    feedback = TranscriptionFeedback(
        user_id=current_user.id,
        message_id=correction.message_id,
        audio_hash=correction.audio_hash,
        incorrect_transcription=correction.incorrect_transcription,
        correct_transcription=correction.correct_transcription,
        language=correction.language,
        confidence_score=correction.confidence_score,
        dialect=correction.dialect,
        metadata=correction.metadata
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.post(
    "/negotiation",
    response_model=NegotiationFeedbackResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_negotiation_feedback(
    feedback_data: NegotiationFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on negotiation suggestions.
    
    Requirements: 20.2, 22.4
    
    This endpoint collects user feedback on the helpfulness and cultural
    appropriateness of negotiation suggestions provided by Sauda Bot.
    """
    feedback = NegotiationFeedback(
        user_id=current_user.id,
        conversation_id=feedback_data.conversation_id,
        suggestion_id=feedback_data.suggestion_id,
        suggested_price=feedback_data.suggested_price,
        suggested_message=feedback_data.suggested_message,
        rating=feedback_data.rating,
        was_helpful=feedback_data.was_helpful,
        was_culturally_appropriate=feedback_data.was_culturally_appropriate,
        was_used=feedback_data.was_used,
        feedback_text=feedback_data.feedback_text,
        commodity=feedback_data.commodity,
        market_average=feedback_data.market_average,
        language=feedback_data.language,
        region=feedback_data.region,
        metadata=feedback_data.metadata
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.post(
    "/satisfaction-survey",
    response_model=SatisfactionSurveyResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_satisfaction_survey(
    survey: SatisfactionSurveyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a voice-based satisfaction survey.
    
    Requirements: 22.1, 22.3
    
    This endpoint collects periodic satisfaction surveys from users,
    asking them to rate their experience with various platform features.
    """
    survey_record = SatisfactionSurvey(
        user_id=current_user.id,
        survey_type=survey.survey_type,
        transaction_id=survey.transaction_id,
        conversation_id=survey.conversation_id,
        overall_rating=survey.overall_rating,
        voice_translation_rating=survey.voice_translation_rating,
        price_oracle_rating=survey.price_oracle_rating,
        negotiation_assistant_rating=survey.negotiation_assistant_rating,
        price_oracle_helpful=survey.price_oracle_helpful,
        negotiation_suggestions_helpful=survey.negotiation_suggestions_helpful,
        negotiation_culturally_appropriate=survey.negotiation_culturally_appropriate,
        feedback_text=survey.feedback_text,
        language=survey.language,
        metadata=survey.metadata
    )
    
    db.add(survey_record)
    db.commit()
    db.refresh(survey_record)
    
    return survey_record


@router.post(
    "/translation",
    response_model=TranslationFeedbackResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_translation_feedback(
    feedback_data: TranslationFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on translation quality.
    
    Requirements: 20.2
    
    This endpoint allows users to rate translation quality and provide
    corrections for improving the translation models.
    """
    feedback = TranslationFeedback(
        user_id=current_user.id,
        message_id=feedback_data.message_id,
        source_text=feedback_data.source_text,
        translated_text=feedback_data.translated_text,
        source_language=feedback_data.source_language,
        target_language=feedback_data.target_language,
        rating=feedback_data.rating,
        was_accurate=feedback_data.was_accurate,
        preserved_meaning=feedback_data.preserved_meaning,
        corrected_translation=feedback_data.corrected_translation,
        feedback_text=feedback_data.feedback_text,
        metadata=feedback_data.metadata
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.post(
    "/price-oracle",
    response_model=PriceOracleFeedbackResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_price_oracle_feedback(
    feedback_data: PriceOracleFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on Price Oracle helpfulness.
    
    Requirements: 22.3
    
    This endpoint collects user feedback on whether the Fair Price Oracle
    was helpful in making trading decisions.
    """
    feedback = PriceOracleFeedback(
        user_id=current_user.id,
        transaction_id=feedback_data.transaction_id,
        conversation_id=feedback_data.conversation_id,
        commodity=feedback_data.commodity,
        quoted_price=feedback_data.quoted_price,
        market_average=feedback_data.market_average,
        price_verdict=feedback_data.price_verdict,
        was_helpful=feedback_data.was_helpful,
        was_accurate=feedback_data.was_accurate,
        influenced_decision=feedback_data.influenced_decision,
        rating=feedback_data.rating,
        feedback_text=feedback_data.feedback_text,
        metadata=feedback_data.metadata
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.post(
    "/voice-survey/initiate",
    response_model=VoiceSurveyPrompt
)
async def initiate_voice_survey(
    request: VoiceSurveyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate a voice-based satisfaction survey.
    
    Requirements: 22.1
    
    This endpoint returns voice prompts for conducting a satisfaction survey.
    The prompts are in the user's preferred language and guide them through
    rating their experience.
    """
    # Generate survey prompts based on survey type
    prompts = _generate_survey_prompts(
        survey_type=request.survey_type,
        language=request.language
    )
    
    # Return the first prompt
    # In a real implementation, this would be part of a multi-step flow
    return prompts[0]


@router.get(
    "/transcription-corrections",
    response_model=List[TranscriptionCorrectionResponse]
)
async def get_user_transcription_corrections(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's transcription corrections.
    
    This endpoint allows users to view their submitted transcription corrections.
    """
    corrections = db.query(TranscriptionFeedback).filter(
        TranscriptionFeedback.user_id == current_user.id
    ).order_by(
        TranscriptionFeedback.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return corrections


@router.get(
    "/negotiation-feedback",
    response_model=List[NegotiationFeedbackResponse]
)
async def get_user_negotiation_feedback(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's negotiation feedback submissions.
    
    This endpoint allows users to view their submitted negotiation feedback.
    """
    feedback = db.query(NegotiationFeedback).filter(
        NegotiationFeedback.user_id == current_user.id
    ).order_by(
        NegotiationFeedback.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return feedback


@router.get(
    "/satisfaction-surveys",
    response_model=List[SatisfactionSurveyResponse]
)
async def get_user_satisfaction_surveys(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's satisfaction survey submissions.
    
    This endpoint allows users to view their submitted satisfaction surveys.
    """
    surveys = db.query(SatisfactionSurvey).filter(
        SatisfactionSurvey.user_id == current_user.id
    ).order_by(
        SatisfactionSurvey.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return surveys


def _generate_survey_prompts(survey_type: str, language: str) -> List[VoiceSurveyPrompt]:
    """
    Generate voice survey prompts based on survey type and language.
    
    In a real implementation, this would:
    1. Load prompts from a database or configuration
    2. Use TTS to generate audio prompts
    3. Support all 22 Indian languages
    
    For now, returns English prompts as examples.
    """
    if survey_type == "post_transaction":
        return [
            VoiceSurveyPrompt(
                prompt_text="How satisfied are you with your recent transaction? Please rate from 1 to 5, where 1 is very dissatisfied and 5 is very satisfied.",
                expected_response_type="rating",
                options=["1", "2", "3", "4", "5"]
            ),
            VoiceSurveyPrompt(
                prompt_text="Was the Fair Price Oracle helpful in your decision? Please say yes or no.",
                expected_response_type="boolean",
                options=["yes", "no"]
            ),
            VoiceSurveyPrompt(
                prompt_text="Were the negotiation suggestions culturally appropriate? Please say yes or no.",
                expected_response_type="boolean",
                options=["yes", "no"]
            )
        ]
    elif survey_type == "periodic":
        return [
            VoiceSurveyPrompt(
                prompt_text="How would you rate your overall experience with Multilingual Mandi? Please rate from 1 to 5.",
                expected_response_type="rating",
                options=["1", "2", "3", "4", "5"]
            ),
            VoiceSurveyPrompt(
                prompt_text="How would you rate the voice translation quality? Please rate from 1 to 5.",
                expected_response_type="rating",
                options=["1", "2", "3", "4", "5"]
            )
        ]
    else:
        return [
            VoiceSurveyPrompt(
                prompt_text="Please provide your feedback.",
                expected_response_type="text",
                options=None
            )
        ]
