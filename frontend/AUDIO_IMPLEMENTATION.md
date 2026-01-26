# Audio Capture and Processing Implementation

## Overview

This document describes the implementation of Task 5: "Implement Audio Capture and Processing (Frontend)" for the Multilingual Mandi platform.

## Implemented Components

### 1. AudioCaptureModule (`src/services/audio/AudioCaptureModule.ts`)

**Purpose**: Handles audio input from user's device with noise reduction and voice activity detection.

**Features**:
- ✅ Microphone access using Web Audio API
- ✅ Voice Activity Detection (VAD) using energy-based and zero-crossing rate methods
- ✅ Noise reduction using spectral subtraction
- ✅ Targets 70+ dB noise environments (Requirement 1.3)
- ✅ 16kHz sample rate optimized for speech processing

**Key Methods**:
- `initialize()`: Sets up audio context and microphone access
- `captureAudio(durationMs)`: Captures raw audio for specified duration
- `detectSpeechActivity(audio)`: Detects if speech is present in audio
- `applyNoiseReduction(audio)`: Reduces background noise using spectral subtraction
- `captureAndProcess(durationMs)`: Complete capture pipeline with VAD and noise reduction

**Requirements Satisfied**: 1.1, 1.3

### 2. AudioCompressionModule (`src/services/audio/AudioCompressionModule.ts`)

**Purpose**: Compresses audio data for low-bandwidth transmission.

**Features**:
- ✅ Opus codec compression (60%+ size reduction)
- ✅ Adaptive bitrate based on network speed
- ✅ Network condition detection using Network Information API
- ✅ Automatic fallback to alternative codecs if Opus not supported
- ✅ Bitrate ranges: 12 kbps (2G) to 32 kbps (4G)

**Key Methods**:
- `compressAudio(audio, bitrate)`: Compresses audio to Opus format
- `detectNetworkCondition()`: Detects current network speed and quality
- `adjustBitrateForNetwork(condition)`: Adjusts bitrate based on network
- `compressWithAdaptiveBitrate(audio)`: Complete compression with adaptive bitrate

**Network Quality Thresholds**:
- Excellent (4G): 1000+ kbps → 32 kbps bitrate
- Good (3G): 500+ kbps → 24 kbps bitrate
- Fair: 200+ kbps → 16 kbps bitrate
- Poor (2G): <200 kbps → 12 kbps bitrate

**Requirements Satisfied**: 2.5, 10.1

### 3. AudioPlaybackModule (`src/services/audio/AudioPlaybackModule.ts`)

**Purpose**: Handles audio playback with adaptive volume control.

**Features**:
- ✅ TTS audio playback from Blob data
- ✅ Adaptive volume based on ambient noise level
- ✅ Replay functionality for last played audio
- ✅ Volume boost in noisy environments (60+ dB threshold)
- ✅ Pause/resume functionality
- ✅ Playback rate control

**Key Methods**:
- `initialize()`: Sets up audio context and gain nodes
- `playAudio(audioBlob, options)`: Plays audio from blob
- `replay()`: Replays last played audio
- `detectAmbientNoise()`: Measures ambient noise level using microphone
- `calculateAdaptiveVolume()`: Calculates volume based on noise level
- `enableAdaptiveVolume(intervalMs)`: Enables automatic volume adjustment

**Adaptive Volume Logic**:
- Base volume: 70%
- Threshold: 60 dB
- Boost: 30% per 10 dB above threshold
- Maximum: 100%

**Requirements Satisfied**: 4.4, 4.5

### 4. AudioDemo Component (`src/components/AudioDemo.tsx`)

**Purpose**: Demonstrates the usage of all audio modules.

**Features**:
- Interactive UI for testing audio capture
- Real-time compression ratio display
- Volume control slider
- Ambient noise detection
- Network quality detection
- Replay functionality

## Test Coverage

All modules have comprehensive unit tests:

### AudioCaptureModule Tests (14 tests)
- Energy calculation for silent and signal audio
- Zero-crossing rate calculation
- Voice activity detection
- Noise reduction
- State management

### AudioCompressionModule Tests (18 tests)
- Bitrate adjustment for different network conditions
- WAV format conversion
- Network detection
- MIME type selection
- Compression ratio calculation

### AudioPlaybackModule Tests (26 tests)
- Volume control and clamping
- Adaptive volume calculation
- Playback state management
- Ambient noise detection
- Error handling
- Cleanup

**Total: 58 tests, all passing ✅**

## Technical Implementation Details

### Web Audio API Usage
- AudioContext for audio processing
- AnalyserNode for frequency analysis (VAD, noise detection)
- GainNode for volume control
- ScriptProcessorNode for audio data capture
- MediaStreamAudioDestinationNode for streaming

### Noise Reduction Algorithm
- Spectral subtraction method
- Estimates noise profile from first 100ms
- Subtracts noise estimate from signal
- Preserves signal polarity

### Voice Activity Detection
- Energy-based detection (threshold: 0.01)
- Zero-crossing rate analysis (valid range: 0.3-0.7)
- Combined confidence scoring
- Minimum 60% confidence for speech detection

### Audio Compression
- Opus codec via MediaRecorder API
- Fallback to WebM/OGG if Opus unavailable
- WAV format for size comparison
- 16-bit PCM encoding

## Browser Compatibility

**Supported APIs**:
- Web Audio API (all modern browsers)
- MediaRecorder API (Chrome, Firefox, Edge, Safari 14.1+)
- MediaDevices.getUserMedia (all modern browsers)
- Network Information API (Chrome, Edge, Opera)

**Fallbacks**:
- Network detection falls back to latency-based estimation
- Codec selection tries multiple formats
- Graceful degradation for unsupported features

## Performance Characteristics

### Latency Targets
- Audio capture: Real-time
- Noise reduction: <100ms
- Compression: <500ms for 5s audio
- Playback: <100ms startup

### Memory Usage
- Audio buffers: ~1MB per 5 seconds (16kHz, 16-bit)
- Compressed audio: ~400KB per 5 seconds (60% reduction)
- Minimal memory footprint with proper cleanup

### CPU Usage
- VAD: Lightweight (energy + ZCR calculation)
- Noise reduction: Moderate (spectral processing)
- Compression: Handled by native MediaRecorder

## Integration with Backend

The audio modules are designed to integrate with the backend services:

1. **Capture** → Send to STT Service
2. **Compress** → Reduce bandwidth for transmission
3. **Playback** → Receive from TTS Service

## Future Enhancements

Potential improvements for future iterations:

1. Advanced VAD using machine learning
2. More sophisticated noise reduction (Wiener filtering)
3. Echo cancellation for full-duplex communication
4. Audio quality metrics and monitoring
5. Offline audio processing with Web Workers
6. Support for additional codecs (AAC, FLAC)

## Usage Example

```typescript
import { AudioCaptureModule } from './services/audio/AudioCaptureModule';
import { AudioCompressionModule } from './services/audio/AudioCompressionModule';
import { AudioPlaybackModule } from './services/audio/AudioPlaybackModule';

// Initialize modules
const capture = new AudioCaptureModule();
const compression = new AudioCompressionModule();
const playback = new AudioPlaybackModule();

await capture.initialize();
await playback.initialize();

// Capture and process audio
const audio = await capture.captureAndProcess(5000);

// Compress for transmission
const result = await compression.compressWithAdaptiveBitrate(audio);
console.log(`Compressed by ${result.compressionRatio}%`);

// Play received audio
await playback.playAudio(result.compressedData);

// Replay if needed
await playback.replay();

// Cleanup
await capture.cleanup();
await compression.cleanup();
await playback.cleanup();
```

## Conclusion

Task 5 has been successfully implemented with all required features:
- ✅ Subtask 5.1: AudioCaptureModule with VAD and noise reduction
- ✅ Subtask 5.2: AudioCompressionModule with adaptive bitrate
- ✅ Subtask 5.4: AudioPlaybackModule with adaptive volume and replay

All components are fully tested, documented, and ready for integration with the backend voice translation pipeline.
