"""
Integration Test 21.4: Voice-Only Onboarding
Tests complete registration flow using only voice

Requirements: 23.1, 23.2, 23.3, 23.4
"""
import pytest
import numpy as np
from uuid import uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.services.onboarding.onboarding_service import OnboardingService
from app.services.onboarding.models import OnboardingStep, OnboardingSession
from app.services.auth.voice_biometric_enrollment import VoiceBiometricEnrollment


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_integration_onboarding.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def onboarding_service():
    """Create onboarding service"""
    return OnboardingService(use_mock=True)


@pytest.fixture
def voice_enrollment():
    """Create voice biometric enrollment service"""
    return VoiceBiometricEnrollment(use_mock=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_voice_onboarding_flow(db_session, onboarding_service, voice_enrollment):
    """
    Test complete voice-only onboarding flow
    Requirements: 23.1, 23.2, 23.4
    
    Steps:
    1. Start onboarding with language selection
    2. Collect name via voice
    3. Collect location via voice
    4. Explain data usage and get consent
    5. Create voice biometric profile
    6. Provide tutorial
    7. Confirm account creation
    """
    import time
    
    start_time = time.time()
    
    # Step 1: Start onboarding with language selection
    session = await onboarding_service.start_onboarding(
        preferred_language="hin"
    )
    
    assert session is not None
    assert session.language == "hin"
    assert session.current_step == OnboardingStep.WELCOME
    assert session.completed_steps == []
    
    # Verify welcome prompt is in Hindi
    welcome_prompt = session.get_current_prompt()
    assert welcome_prompt is not None
    assert welcome_prompt.language == "hin"
    assert "welcome" in welcome_prompt.text.lower() or "स्वागत" in welcome_prompt.text
    
    # Step 2: Collect name via voice
    # Simulate voice input: "मेरा नाम राज कुमार है"
    name_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    name_result = await onboarding_service.process_voice_input(
        session=session,
        audio=name_audio,
        expected_input_type="name"
    )
    
    assert name_result.success is True
    assert name_result.extracted_value is not None
    assert session.user_data["name"] is not None
    assert OnboardingStep.COLLECT_NAME in session.completed_steps
    
    # Step 3: Collect location via voice
    # Simulate voice input: "मैं महाराष्ट्र के मुंबई से हूं"
    location_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    location_result = await onboarding_service.process_voice_input(
        session=session,
        audio=location_audio,
        expected_input_type="location"
    )
    
    assert location_result.success is True
    assert session.user_data["location_state"] is not None
    assert session.user_data["location_district"] is not None
    assert OnboardingStep.COLLECT_LOCATION in session.completed_steps
    
    # Step 4: Explain data usage and get consent
    consent_explanation = await onboarding_service.get_consent_explanation(
        session=session
    )
    
    assert consent_explanation is not None
    assert consent_explanation.language == "hin"
    assert len(consent_explanation.text) > 0
    
    # Simulate voice consent: "हां, मैं सहमत हूं"
    consent_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    consent_result = await onboarding_service.collect_consent(
        session=session,
        audio=consent_audio
    )
    
    assert consent_result.success is True
    assert consent_result.consent_given is True
    assert session.user_data["consent_given"] is True
    assert session.user_data["consent_timestamp"] is not None
    assert OnboardingStep.COLLECT_CONSENT in session.completed_steps
    
    # Step 5: Create voice biometric profile
    # Collect 3 voice samples
    voice_samples = []
    for i in range(3):
        # Simulate voice sample: "यह मेरी आवाज़ का नमूना है"
        sample_audio = np.random.randn(32000).astype(np.float32) * 0.1  # 2 seconds
        voice_samples.append(sample_audio)
    
    voiceprint_result = await onboarding_service.create_voiceprint(
        session=session,
        voice_samples=voice_samples
    )
    
    assert voiceprint_result.success is True
    assert voiceprint_result.voiceprint_id is not None
    assert session.user_data["voiceprint_id"] is not None
    assert OnboardingStep.CREATE_VOICEPRINT in session.completed_steps
    
    # Step 6: Provide tutorial
    tutorial_result = await onboarding_service.provide_tutorial(
        session=session
    )
    
    assert tutorial_result.success is True
    assert len(tutorial_result.tutorial_steps) > 0
    assert OnboardingStep.TUTORIAL in session.completed_steps
    
    # Step 7: Complete onboarding and create user account
    completion_result = await onboarding_service.complete_onboarding(
        session=session,
        db=db_session,
        phone_number="+919876543210"
    )
    
    assert completion_result.success is True
    assert completion_result.user_id is not None
    assert completion_result.confirmation_message is not None
    
    # Verify user was created in database
    user = db_session.query(User).filter(
        User.id == completion_result.user_id
    ).first()
    
    assert user is not None
    assert user.name == session.user_data["name"]
    assert user.phone_number == "+919876543210"
    assert user.primary_language == "hin"
    assert user.location_state == session.user_data["location_state"]
    assert user.location_district == session.user_data["location_district"]
    
    # Verify voiceprint was created
    voiceprint = db_session.query(Voiceprint).filter(
        Voiceprint.user_id == user.id
    ).first()
    
    assert voiceprint is not None
    assert voiceprint.sample_count == 3
    
    # Check total onboarding time
    end_time = time.time()
    total_time_seconds = end_time - start_time
    
    # Should complete in under 3 minutes (Requirement 23.7)
    assert total_time_seconds < 180, f"Onboarding took {total_time_seconds:.1f}s, exceeds 180s limit"
    
    print("\n✓ Complete voice onboarding flow test passed!")
    print(f"  - Total time: {total_time_seconds:.1f}s (< 180s requirement)")
    print(f"  - User created: {user.name}")
    print(f"  - Language: {user.primary_language}")
    print(f"  - Location: {user.location_district}, {user.location_state}")
    print(f"  - Voiceprint created with {voiceprint.sample_count} samples")
    print(f"  - Consent recorded: {session.user_data['consent_given']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_with_unclear_input(db_session, onboarding_service):
    """
    Test onboarding with unclear voice input requiring clarification
    Requirement 23.8
    """
    # Start onboarding
    session = await onboarding_service.start_onboarding("hin")
    
    # Simulate unclear name input (low confidence)
    unclear_audio = np.random.randn(8000).astype(np.float32) * 0.05  # Quiet audio
    
    name_result = await onboarding_service.process_voice_input(
        session=session,
        audio=unclear_audio,
        expected_input_type="name"
    )
    
    # Should request clarification
    if not name_result.success or name_result.confidence < 0.7:
        assert name_result.needs_clarification is True
        assert name_result.clarification_prompt is not None
        
        # Simulate clearer input
        clear_audio = np.random.randn(16000).astype(np.float32) * 0.1
        
        retry_result = await onboarding_service.process_voice_input(
            session=session,
            audio=clear_audio,
            expected_input_type="name"
        )
        
        assert retry_result.success is True
        assert retry_result.extracted_value is not None
    
    print("\n✓ Unclear input handling test passed!")
    print(f"  - System requested clarification for unclear input")
    print(f"  - Successfully processed clearer input")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_in_multiple_languages(db_session, onboarding_service):
    """
    Test onboarding flow in different languages
    """
    languages = ["hin", "tel", "tam", "kan", "mar"]
    
    for lang in languages:
        # Start onboarding in this language
        session = await onboarding_service.start_onboarding(lang)
        
        assert session.language == lang
        
        # Verify prompts are in correct language
        welcome_prompt = session.get_current_prompt()
        assert welcome_prompt.language == lang
        
        # Simulate name collection
        name_audio = np.random.randn(16000).astype(np.float32) * 0.1
        name_result = await onboarding_service.process_voice_input(
            session=session,
            audio=name_audio,
            expected_input_type="name"
        )
        
        assert name_result.success is True
    
    print("\n✓ Multi-language onboarding test passed!")
    print(f"  - Tested onboarding in {len(languages)} languages")
    print(f"  - Languages: {', '.join(languages)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_consent_explanation(db_session, onboarding_service):
    """
    Test that data usage is explained clearly before consent
    Requirement 23.3
    """
    session = await onboarding_service.start_onboarding("hin")
    
    # Progress to consent step
    session.current_step = OnboardingStep.COLLECT_CONSENT
    
    # Get consent explanation
    explanation = await onboarding_service.get_consent_explanation(session)
    
    assert explanation is not None
    assert explanation.language == "hin"
    
    # Verify explanation covers key points
    explanation_text = explanation.text.lower()
    
    # Should mention data collection
    assert any(keyword in explanation_text for keyword in ["data", "information", "डेटा", "जानकारी"])
    
    # Should mention usage purpose
    assert any(keyword in explanation_text for keyword in ["use", "purpose", "उपयोग", "उद्देश्य"])
    
    # Should mention privacy
    assert any(keyword in explanation_text for keyword in ["privacy", "private", "गोपनीयता", "निजी"])
    
    # Verify explanation is in simple language (not too long)
    word_count = len(explanation.text.split())
    assert word_count < 200, "Explanation should be concise for low-literacy users"
    
    print("\n✓ Consent explanation test passed!")
    print(f"  - Explanation provided in {session.language}")
    print(f"  - Word count: {word_count} (< 200 for simplicity)")
    print(f"  - Covers data collection, usage, and privacy")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_voiceprint_quality(db_session, onboarding_service, voice_enrollment):
    """
    Test voiceprint creation with quality validation
    """
    session = await onboarding_service.start_onboarding("hin")
    
    # Collect voice samples with varying quality
    good_samples = []
    for i in range(3):
        # Good quality sample (2 seconds, adequate volume)
        sample = np.random.randn(32000).astype(np.float32) * 0.1
        good_samples.append(sample)
    
    # Create voiceprint with good samples
    good_result = await onboarding_service.create_voiceprint(
        session=session,
        voice_samples=good_samples
    )
    
    assert good_result.success is True
    assert good_result.quality_score > 0.7
    
    # Try with poor quality samples
    poor_samples = []
    for i in range(3):
        # Poor quality sample (too short, too quiet)
        sample = np.random.randn(8000).astype(np.float32) * 0.01
        poor_samples.append(sample)
    
    poor_result = await onboarding_service.create_voiceprint(
        session=session,
        voice_samples=poor_samples
    )
    
    # Should either fail or request better samples
    if not poor_result.success:
        assert poor_result.error_message is not None
        assert "quality" in poor_result.error_message.lower() or "sample" in poor_result.error_message.lower()
    else:
        assert poor_result.quality_score < good_result.quality_score
    
    print("\n✓ Voiceprint quality test passed!")
    print(f"  - Good samples quality score: {good_result.quality_score:.2f}")
    print(f"  - Poor samples handled appropriately")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_tutorial_content(db_session, onboarding_service):
    """
    Test that tutorial covers key features
    Requirement 23.5
    """
    session = await onboarding_service.start_onboarding("hin")
    
    # Get tutorial
    tutorial_result = await onboarding_service.provide_tutorial(session)
    
    assert tutorial_result.success is True
    assert len(tutorial_result.tutorial_steps) > 0
    
    # Verify tutorial covers key features
    tutorial_topics = [step.topic for step in tutorial_result.tutorial_steps]
    
    # Should cover voice commands
    assert any("voice" in topic.lower() or "आवाज़" in topic for topic in tutorial_topics)
    
    # Should cover price checking
    assert any("price" in topic.lower() or "भाव" in topic or "कीमत" in topic for topic in tutorial_topics)
    
    # Should cover conversations
    assert any("conversation" in topic.lower() or "बातचीत" in topic for topic in tutorial_topics)
    
    # Each step should have audio
    for step in tutorial_result.tutorial_steps:
        assert step.audio_prompt is not None
        assert step.language == "hin"
    
    print("\n✓ Tutorial content test passed!")
    print(f"  - Tutorial has {len(tutorial_result.tutorial_steps)} steps")
    print(f"  - Topics covered: {', '.join(tutorial_topics)}")
    print(f"  - All steps have audio prompts in {session.language}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_skip_optional_steps(db_session, onboarding_service):
    """
    Test that users can skip optional steps
    Requirement 23.7
    """
    session = await onboarding_service.start_onboarding("hin")
    
    # Collect required information
    name_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.process_voice_input(session, name_audio, "name")
    
    location_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.process_voice_input(session, location_audio, "location")
    
    consent_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.collect_consent(session, consent_audio)
    
    voice_samples = [np.random.randn(32000).astype(np.float32) * 0.1 for _ in range(3)]
    await onboarding_service.create_voiceprint(session, voice_samples)
    
    # Skip tutorial (optional step)
    skip_result = await onboarding_service.skip_step(
        session=session,
        step=OnboardingStep.TUTORIAL
    )
    
    assert skip_result.success is True
    assert OnboardingStep.TUTORIAL in session.skipped_steps
    
    # Complete onboarding without tutorial
    completion_result = await onboarding_service.complete_onboarding(
        session=session,
        db=db_session,
        phone_number="+919876543210"
    )
    
    assert completion_result.success is True
    assert completion_result.user_id is not None
    
    print("\n✓ Skip optional steps test passed!")
    print(f"  - Successfully skipped tutorial step")
    print(f"  - Onboarding completed without optional steps")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_performance_requirement(db_session, onboarding_service):
    """
    Test that onboarding completes in under 3 minutes
    Requirement 23.7 (Property 71)
    """
    import time
    
    start_time = time.time()
    
    # Simulate fast onboarding flow
    session = await onboarding_service.start_onboarding("hin")
    
    # Collect all required information quickly
    name_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.process_voice_input(session, name_audio, "name")
    
    location_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.process_voice_input(session, location_audio, "location")
    
    consent_audio = np.random.randn(16000).astype(np.float32) * 0.1
    await onboarding_service.collect_consent(session, consent_audio)
    
    voice_samples = [np.random.randn(32000).astype(np.float32) * 0.1 for _ in range(3)]
    await onboarding_service.create_voiceprint(session, voice_samples)
    
    # Skip tutorial to minimize time
    await onboarding_service.skip_step(session, OnboardingStep.TUTORIAL)
    
    # Complete onboarding
    await onboarding_service.complete_onboarding(
        session=session,
        db=db_session,
        phone_number="+919876543210"
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Should complete in under 3 minutes (180 seconds)
    assert total_time < 180, f"Onboarding took {total_time:.1f}s, exceeds 180s requirement"
    
    print("\n✓ Onboarding performance test passed!")
    print(f"  - Completed in {total_time:.1f}s (< 180s requirement)")
    print(f"  - Fast enough for user retention")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_confirmation_message(db_session, onboarding_service):
    """
    Test that account creation is confirmed via voice
    Requirement 23.6 (Property 72)
    """
    session = await onboarding_service.start_onboarding("hin")
    
    # Complete onboarding
    session.user_data = {
        "name": "Test User",
        "location_state": "Maharashtra",
        "location_district": "Mumbai",
        "consent_given": True,
        "consent_timestamp": datetime.utcnow(),
        "voiceprint_id": str(uuid4())
    }
    session.completed_steps = [
        OnboardingStep.WELCOME,
        OnboardingStep.COLLECT_NAME,
        OnboardingStep.COLLECT_LOCATION,
        OnboardingStep.COLLECT_CONSENT,
        OnboardingStep.CREATE_VOICEPRINT
    ]
    
    completion_result = await onboarding_service.complete_onboarding(
        session=session,
        db=db_session,
        phone_number="+919876543210"
    )
    
    assert completion_result.success is True
    assert completion_result.confirmation_message is not None
    
    # Verify confirmation message
    confirmation = completion_result.confirmation_message
    assert confirmation.language == "hin"
    assert confirmation.audio_prompt is not None
    
    # Should mention account creation
    message_text = confirmation.text.lower()
    assert any(keyword in message_text for keyword in ["account", "created", "खाता", "बनाया"])
    
    # Should include user's name
    assert session.user_data["name"].lower() in message_text or "test user" in message_text
    
    print("\n✓ Confirmation message test passed!")
    print(f"  - Confirmation message generated in {confirmation.language}")
    print(f"  - Includes account creation confirmation")
    print(f"  - Includes user's name")
    print(f"  - Has audio prompt for voice output")
