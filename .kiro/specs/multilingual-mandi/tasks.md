# Implementation Plan: Multilingual Mandi

## Overview

This implementation plan breaks down the Multilingual Mandi platform into discrete, incremental coding tasks. The platform will be built using Python (FastAPI) for backend services and TypeScript (React) for the frontend PWA. Tasks are organized to deliver core functionality early with progressive enhancement.

**Technology Stack**:
- Backend: Python 3.11+ with FastAPI
- Frontend: React 18+ with TypeScript
- AI/ML: AI4Bharat models (IndicWhisper, IndicTrans2, Indic-TTS)
- Database: PostgreSQL 15+
- Cache: Redis
- Testing: Pytest (Python), Vitest (TypeScript), Hypothesis (property-based testing)

## Tasks

- [x] 1. Project Setup and Infrastructure
  - Set up monorepo structure with backend and frontend directories
  - Configure Python virtual environment and install FastAPI, SQLAlchemy, Redis client
  - Configure TypeScript React project with Vite, PWA support (Workbox)
  - Set up Docker Compose for local development (PostgreSQL, Redis)
  - Create initial database schema and migrations
  - Set up environment configuration management
  - _Requirements: 19.1, 19.2, 19.3, 19.5_

- [x] 2. Implement Demo Price Data Provider
  - [x] 2.1 Create demo data models and structures
    - Implement `CommodityPriceData` class with base prices, seasonal factors, regional variations
    - Create demo data for 50+ common agricultural commodities (tomato, onion, potato, rice, wheat, etc.)
    - Implement seasonal price variation logic based on month
    - _Requirements: 6.4, 6.5_
  
  - [x] 2.2 Write property test for demo price generation

    - **Property 21: Price Data Completeness**
    - **Validates: Requirements 6.5**
  
  - [x] 2.3 Implement `DemoDataProvider` class
    - Create methods for generating realistic price data with random variation (±10%)
    - Implement regional price adjustments for different states
    - Add fallback for unknown commodities
    - _Requirements: 6.1, 6.2, 6.7_
  
  - [x] 2.4 Write unit tests for demo data provider

    - Test seasonal factor calculations
    - Test regional variations
    - Test price generation with variation
    - _Requirements: 6.1, 6.2_

- [x] 3. Implement Fair Price Oracle Core
  - [x] 3.1 Create `PriceDataAggregator` with fallback strategy
    - Implement multi-source price fetching (eNAM, mandi boards, crowd-sourced, demo)
    - Implement fallback logic: eNAM → State Mandi → Crowd-sourced → Demo
    - Add error handling for API unavailability
    - _Requirements: 6.1, 6.2, 6.6_
  
  - [x] 3.2 Implement `PriceComparisonEngine`
    - Create price classification logic (fair within 5%, high >10%, low >10%)
    - Implement `analyze_quote` method with market average comparison
    - Generate user-friendly comparison messages
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 3.3 Write property test for price classification

    - **Property 22: Price Classification Logic**
    - **Validates: Requirements 7.2, 7.3, 7.4**
  
  - [x] 3.4 Implement `PriceCacheManager` with Redis
    - Create caching logic with 1-hour TTL
    - Implement cache retrieval and invalidation
    - Add offline cache support (24-hour TTL)
    - _Requirements: 6.1, 12.2_
  
  - [x] 3.5 Write property test for price caching

    - **Property 33: Data Caching for Offline Access**
    - **Validates: Requirements 10.4, 12.2**

- [x] 4. Checkpoint - Test Price Oracle
  - Ensure all tests pass for demo data and price comparison
  - Manually test price queries with various commodities
  - Ask the user if questions arise

- [x] 5. Implement Audio Capture and Processing (Frontend)
  - [x] 5.1 Create `AudioCaptureModule` component
    - Implement microphone access using Web Audio API
    - Add Voice Activity Detection (VAD) for speech detection
    - Implement noise reduction using spectral subtraction
    - _Requirements: 1.1, 1.3_
  
  - [x] 5.2 Implement audio compression for low bandwidth
    - Compress audio to reduce size by 60%+ using Opus codec
    - Implement adaptive bitrate based on network speed
    - _Requirements: 2.5, 10.1_
  
  - [x] 5.3 Write property test for audio compression

    - **Property 9: Audio Compression for Low Bandwidth**
    - **Validates: Requirements 2.5, 10.1**
  
  - [x] 5.4 Create audio playback component with volume control
    - Implement TTS audio playback
    - Add adaptive volume based on ambient noise
    - Add replay functionality
    - _Requirements: 4.4, 4.5_

- [x] 6. Implement Speech-to-Text Service (Backend)
  - [x] 6.1 Set up AI4Bharat IndicWhisper model
    - Download and load IndicWhisper model
    - Configure model for 22 Indian languages
    - Implement model inference pipeline
    - _Requirements: 1.5, 2.6_
  
  - [x] 6.2 Create `STTService` class
    - Implement `transcribe` method with language parameter
    - Add confidence scoring and low-confidence handling
    - Implement domain vocabulary boosting for commodity terms
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 6.3 Write property test for STT latency
    - **Property 5: Speech-to-Text Latency**
    - **Validates: Requirements 2.1**
  
  - [ ]* 6.4 Write property test for low-confidence handling
    - **Property 7: Low-Confidence Transcription Handling**
    - **Validates: Requirements 2.3**

- [x] 7. Implement Translation Service (Backend)
  - [x] 7.1 Set up AI4Bharat IndicTrans2 model
    - Download and load IndicTrans2 models (Indic-Indic, En-Indic, Indic-En)
    - Configure tokenizer for all 22 languages
    - _Requirements: 3.6_
  
  - [x] 7.2 Create `TranslationService` class
    - Implement `translate` method with source and target language
    - Add entity preservation for commodity names, prices, units
    - Implement confidence scoring and flagging
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ]* 7.3 Write property test for translation latency
    - **Property 10: Translation Latency**
    - **Validates: Requirements 3.1**
  
  - [ ]* 7.4 Write property test for entity preservation
    - **Property 11: Entity Preservation in Translation**
    - **Validates: Requirements 3.2**

- [x] 8. Implement Text-to-Speech Service (Backend)
  - [x] 8.1 Set up AI4Bharat Indic-TTS models
    - Download and load TTS models for supported languages
    - Configure voice models for natural speech
    - _Requirements: 4.6_
  
  - [x] 8.2 Create `TTSService` class
    - Implement `synthesize` method with language and speech rate parameters
    - Set speech rate to 85% (15% slower) for clarity
    - Add audio format conversion (MP3 compression)
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 8.3 Write property test for TTS latency
    - **Property 14: Text-to-Speech Latency**
    - **Validates: Requirements 4.1**
  
  - [ ]* 8.4 Write property test for speech rate
    - **Property 15: Speech Rate Adjustment**
    - **Validates: Requirements 4.3**

- [x] 9. Implement Vocal Vernacular Engine Orchestrator
  - [x] 9.1 Create `LanguageDetector` service
    - Implement language detection using Whisper's built-in detection
    - Add code-switching detection for mixed-language speech
    - _Requirements: 1.2, 1.6_
  
  - [x] 9.2 Create `VocalVernacularEngine` orchestrator
    - Implement `process_voice_message` pipeline: Audio → Detect → STT → Translate → TTS
    - Add latency tracking for each stage
    - Implement error handling and retry logic
    - _Requirements: 5.1, 5.3_
  
  - [ ]* 9.3 Write property test for end-to-end latency
    - **Property 1: Voice-to-Voice Translation End-to-End Latency**
    - **Validates: Requirements 5.1**
  
  - [ ]* 9.4 Write property test for language detection
    - **Property 2: Language Detection Accuracy and Speed**
    - **Validates: Requirements 1.2, 1.5**

- [x] 10. Checkpoint - Test Voice Translation Pipeline
  - Ensure all tests pass for voice-to-voice translation
  - Test with sample audio in multiple languages
  - Verify latency is under 8 seconds
  - Ask the user if questions arise

- [ ] 11. Implement Sauda Bot Negotiation Assistant
  - [x] 11.1 Set up LLM (Llama 3.1 8B or Mistral 7B)
    - Download and load quantized LLM model
    - Configure inference parameters for negotiation suggestions
    - _Requirements: 8.6_
  
  - [x] 11.2 Create `NegotiationContextAnalyzer`
    - Extract negotiation state from conversation (commodity, quotes, sentiment)
    - Analyze user relationship (new vs. repeat customer)
    - Implement sentiment detection (friendly, formal, tense)
    - _Requirements: 9.2_
  
  - [x] 11.3 Create `CulturalContextEngine`
    - Load regional norms and honorifics for all languages
    - Implement festival calendar with pricing adjustments
    - Add regional negotiation style preferences
    - _Requirements: 9.1, 9.7, 9.8_
  
  - [x] 11.4 Create `SuggestionGenerator` with LLM
    - Implement prompt building with cultural context
    - Generate counter-offer suggestions within 15% of market average
    - Ensure suggestions include honorifics and relationship terms
    - Filter out aggressive language
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.5_
  
  - [ ]* 11.5 Write property test for counter-offer bounds
    - **Property 25: Counter-Offer Price Bounds**
    - **Validates: Requirements 8.2**
  
  - [ ]* 11.6 Write property test for cultural honorifics
    - **Property 28: Cultural Honorifics Inclusion**
    - **Validates: Requirements 9.1**
  
  - [ ]* 11.7 Write property test for aggressive language avoidance
    - **Property 30: Aggressive Language Avoidance**
    - **Validates: Requirements 9.5**

- [x] 12. Implement Voice Biometric Authentication
  - [x] 12.1 Set up SpeechBrain speaker recognition model
    - Download and load ECAPA-TDNN model for speaker embeddings
    - Configure embedding extraction pipeline
    - _Requirements: 21.7_
  
  - [x] 12.2 Create `VoiceBiometricEnrollment` service
    - Implement voiceprint creation from multiple samples
    - Store voiceprints securely with encryption
    - _Requirements: 21.1, 21.5_
  
  - [x] 12.3 Create `VoiceBiometricVerification` service
    - Implement voice matching with 95% accuracy threshold
    - Add fallback to voice-based PIN
    - Implement anti-spoofing measures
    - _Requirements: 21.2, 21.3, 21.4_
  
  - [ ]* 12.4 Write property test for authentication latency
    - **Property 67: Voice Authentication Latency and Accuracy**
    - **Validates: Requirements 21.2, 21.3**

- [~] 13. Implement User Management and Onboarding
  - [x] 13.1 Create user database models
    - Implement User, UserPreferences, Voiceprint models
    - Create database migrations
    - _Requirements: 15.5_
  
  - [x] 13.2 Create `OnboardingService` with voice-guided flow
    - Implement step-by-step voice prompts for registration
    - Collect name, location, primary language via voice
    - Implement consent collection with explanation
    - Create voice biometric profile during onboarding
    - _Requirements: 23.1, 23.2, 23.3, 23.4_
  
  - [ ]* 13.3 Write property test for onboarding completion time
    - **Property 71: Voice-Based Onboarding Flow**
    - **Validates: Requirements 23.1, 23.2, 23.7**
  
  - [x] 13.4 Implement authentication endpoints
    - Create login/logout endpoints with voice biometric verification
    - Implement session management with JWT tokens
    - _Requirements: 21.2, 21.3_

- [~] 14. Implement Conversation and Transaction Management
  - [x] 14.1 Create conversation database models
    - Implement Conversation, Message, Transaction models
    - Create database migrations
    - _Requirements: 13.1, 16.1_
  
  - [x] 14.2 Create conversation management API
    - Implement endpoints for creating, listing, switching conversations
    - Support up to 5 concurrent conversations per user
    - Maintain separate context for each conversation
    - _Requirements: 16.1, 16.2, 16.3_
  
  - [x] 14.3 Implement transaction recording
    - Store completed transactions with all required fields
    - Implement transaction history retrieval
    - Add voice-based history playback
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ]* 14.4 Write property test for transaction data completeness
    - **Property 39: Transaction Data Completeness**
    - **Validates: Requirements 13.1**

- [~] 15. Implement Offline Functionality (Frontend PWA)
  - [x] 15.1 Configure service worker with Workbox
    - Set up service worker for offline caching
    - Implement cache-first strategy for static assets
    - Add network-first strategy for API calls with fallback
    - _Requirements: 12.7, 19.1_
  
  - [x] 15.2 Create `OfflineSyncManager`
    - Implement message queueing for offline recording
    - Store queued messages in IndexedDB
    - Implement auto-sync when connectivity restored
    - _Requirements: 12.1, 12.3_
  
  - [ ]* 15.3 Write property test for offline message sync
    - **Property 36: Offline Message Recording and Sync**
    - **Validates: Requirements 12.1, 12.3**
  
  - [-] 15.4 Implement offline data caching
    - Cache price data with 24-hour TTL
    - Cache negotiation templates locally
    - Cache transaction history and user preferences
    - _Requirements: 12.2, 12.5, 12.6, 12.8_
  
  - [~] 15.5 Add offline mode detection and notification
    - Detect network status changes
    - Show offline indicator to user
    - Provide voice notification when going offline/online
    - _Requirements: 12.4_

- [~] 16. Implement Voice-First UI Components (Frontend)
  - [~] 16.1 Create voice command handler
    - Implement voice command recognition for navigation
    - Add voice confirmation before executing actions
    - Support commands in all 22 languages
    - _Requirements: 11.2, 11.3_
  
  - [ ]* 16.2 Write property test for voice command coverage
    - **Property 34: Voice Command Coverage and Confirmation**
    - **Validates: Requirements 11.2, 11.3**
  
  - [~] 16.3 Create audio feedback system
    - Implement audio feedback for all system states (loading, error, success)
    - Add voice prompts for all major actions
    - _Requirements: 11.1, 11.4_
  
  - [~] 16.4 Implement conversation UI
    - Create voice-first conversation interface
    - Add visual indicators for processing states
    - Implement conversation switching with voice announcements
    - _Requirements: 5.2, 16.2, 16.4_
  
  - [~] 16.5 Create price check UI
    - Implement voice-activated price queries
    - Display price comparison results with voice output
    - Show data source indicators (official vs. demo)
    - _Requirements: 6.3, 7.5_

- [~] 17. Implement Error Handling and Recovery
  - [~] 17.1 Create `ErrorHandler` service
    - Implement error categorization (network, audio, translation, service, data)
    - Add multilingual error messages
    - Implement corrective action suggestions
    - _Requirements: 14.1, 14.2_
  
  - [~] 17.2 Implement `RetryManager` with exponential backoff
    - Add retry logic for failed service calls (max 3 retries)
    - Implement exponential backoff (1s, 2s, 4s)
    - _Requirements: 14.3_
  
  - [ ]* 17.3 Write property test for retry logic
    - **Property 44: Service Retry Logic**
    - **Validates: Requirements 14.3**
  
  - [~] 17.4 Implement graceful degradation
    - Handle critical service failures without complete system failure
    - Provide available functionality when services are down
    - _Requirements: 14.5_

- [~] 18. Implement Security and Privacy Features
  - [~] 18.1 Configure TLS 1.3 for all API endpoints
    - Set up HTTPS with TLS 1.3
    - Enforce secure connections
    - _Requirements: 15.1_
  
  - [~] 18.2 Implement audio data deletion policy
    - Delete raw audio within 24 hours after processing
    - Implement automated cleanup job
    - _Requirements: 15.2_
  
  - [~] 18.3 Implement data anonymization for third-party sharing
    - Remove PII from data shared for price aggregation
    - Implement anonymization utilities
    - _Requirements: 15.3_
  
  - [~] 18.4 Implement account deletion with data removal
    - Create account deletion endpoint
    - Remove all personal data within 30 days
    - _Requirements: 15.4_
  
  - [~] 18.5 Implement audit logging
    - Log all data access and processing operations
    - Ensure logs don't contain PII
    - _Requirements: 15.10_
  
  - [ ]* 18.6 Write property test for privacy-preserving logging
    - **Property 45: Privacy-Preserving Error Logging**
    - **Validates: Requirements 14.4**

- [~] 19. Implement Monitoring and Feedback Systems
  - [~] 19.1 Create metrics tracking service
    - Track latency for all voice pipeline stages
    - Monitor STT accuracy via user correction rates
    - Track transaction completion vs. abandonment rates
    - _Requirements: 18.1, 18.2, 18.3_
  
  - [~] 19.2 Implement feedback collection
    - Create endpoints for transcription corrections
    - Implement voice-based satisfaction surveys
    - Collect feedback on negotiation suggestions
    - _Requirements: 20.1, 20.2, 22.1, 22.3, 22.4_
  
  - [ ]* 19.3 Write property test for feedback logging
    - **Property 62: Feedback Data Logging**
    - **Validates: Requirements 20.1**
  
  - [~] 19.4 Set up Prometheus and Grafana
    - Configure Prometheus for metrics collection
    - Create Grafana dashboards for monitoring
    - Set up alerts for latency thresholds (>10s)
    - _Requirements: 18.4, 24.7_

- [~] 20. Implement Performance Optimization and Scaling
  - [~] 20.1 Implement load balancing with Nginx
    - Configure Nginx as reverse proxy
    - Set up load balancing across backend instances
    - _Requirements: 24.5_
  
  - [~] 20.2 Implement auto-scaling logic
    - Monitor system load and resource utilization
    - Trigger scaling when load exceeds 80%
    - _Requirements: 24.3_
  
  - [~] 20.3 Optimize bundle size for frontend
    - Implement code splitting and lazy loading
    - Ensure initial page weight < 500 KB
    - _Requirements: 10.5_
  
  - [~] 20.4 Implement adaptive network mode switching
    - Detect network speed
    - Switch to text-only mode when speed < 100 kbps
    - _Requirements: 10.3_

- [ ] 21. Integration Testing and End-to-End Scenarios
  - [ ]* 21.1 Write integration test for complete transaction flow
    - Test Hindi speaker negotiating with Telugu speaker
    - Verify voice translation, price check, and negotiation assistance
    - _Requirements: 1.1, 3.1, 5.1, 7.1, 8.1_
  
  - [ ]* 21.2 Write integration test for offline-to-online transition
    - Test message recording while offline
    - Verify auto-sync when connectivity restored
    - _Requirements: 12.1, 12.3_
  
  - [ ]* 21.3 Write integration test for multi-conversation management
    - Test maintaining 5 concurrent conversations
    - Verify context switching and isolation
    - _Requirements: 16.1, 16.2, 16.3_
  
  - [ ]* 21.4 Write integration test for voice-only onboarding
    - Test complete registration flow using only voice
    - Verify voiceprint creation and authentication
    - _Requirements: 23.1, 23.2, 23.3, 23.4_

- [~] 22. Final Checkpoint - System Integration
  - Run all unit tests and property tests
  - Perform end-to-end testing of all major flows
  - Verify performance requirements (latency, accuracy, concurrency)
  - Test on simulated 2G/3G networks
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (min 100 iterations each)
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: data layer → services → orchestration → UI
- Demo data enables development without external API dependencies
- Voice-first design ensures accessibility for low-literacy users
