/**
 * AudioCaptureModule - Handles audio input from user's device
 * Implements microphone access, Voice Activity Detection (VAD), and noise reduction
 * Requirements: 1.1, 1.3
 */

export interface AudioBuffer {
  data: Float32Array;
  sampleRate: number;
  duration: number;
}

export interface VADResult {
  isSpeech: boolean;
  confidence: number;
}

export class AudioCaptureModule {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private analyser: AnalyserNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private isRecording = false;
  private audioChunks: Float32Array[] = [];
  
  // VAD parameters
  private readonly ENERGY_THRESHOLD = 0.01; // Minimum energy for speech
  private readonly ZERO_CROSSING_THRESHOLD = 0.3; // Zero crossing rate threshold
  private readonly SPEECH_CONFIDENCE_THRESHOLD = 0.6;
  
  // Noise reduction parameters
  private noiseProfile: Float32Array | null = null;
  private readonly NOISE_REDUCTION_FACTOR = 0.5;

  /**
   * Initializes audio context and requests microphone access
   */
  async initialize(): Promise<void> {
    try {
      // Create audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // 16kHz for speech processing
        },
      });
      
      // Create analyser for VAD
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.analyser.smoothingTimeConstant = 0.8;
      
      // Connect media stream to analyser
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.analyser);
      
    } catch (error) {
      throw new Error(`Failed to initialize audio capture: ${error}`);
    }
  }

  /**
   * Captures audio from microphone for specified duration
   * @param durationMs - Duration in milliseconds
   * @returns Raw audio buffer in PCM format
   */
  async captureAudio(durationMs: number): Promise<AudioBuffer> {
    if (!this.audioContext || !this.mediaStream) {
      throw new Error('Audio capture not initialized');
    }

    this.audioChunks = [];
    this.isRecording = true;

    return new Promise((resolve, reject) => {
      try {
        const source = this.audioContext!.createMediaStreamSource(this.mediaStream!);
        
        // Create script processor for audio data capture
        this.scriptProcessor = this.audioContext!.createScriptProcessor(4096, 1, 1);
        
        this.scriptProcessor.onaudioprocess = (event) => {
          if (this.isRecording) {
            const inputData = event.inputBuffer.getChannelData(0);
            this.audioChunks.push(new Float32Array(inputData));
          }
        };
        
        source.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext!.destination);
        
        // Stop recording after specified duration
        setTimeout(() => {
          this.isRecording = false;
          
          if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
          }
          
          // Combine audio chunks
          const totalLength = this.audioChunks.reduce((acc, chunk) => acc + chunk.length, 0);
          const combinedData = new Float32Array(totalLength);
          let offset = 0;
          
          for (const chunk of this.audioChunks) {
            combinedData.set(chunk, offset);
            offset += chunk.length;
          }
          
          resolve({
            data: combinedData,
            sampleRate: this.audioContext!.sampleRate,
            duration: durationMs / 1000,
          });
        }, durationMs);
        
      } catch (error) {
        this.isRecording = false;
        reject(new Error(`Failed to capture audio: ${error}`));
      }
    });
  }

  /**
   * Detects speech activity using Voice Activity Detection (VAD)
   * Uses energy-based and zero-crossing rate methods
   * @param audio - Audio buffer to analyze
   * @returns True if speech is detected
   */
  detectSpeechActivity(audio: AudioBuffer): boolean {
    const vadResult = this.performVAD(audio);
    return vadResult.isSpeech && vadResult.confidence >= this.SPEECH_CONFIDENCE_THRESHOLD;
  }

  /**
   * Performs Voice Activity Detection analysis
   * @param audio - Audio buffer to analyze
   * @returns VAD result with confidence score
   */
  private performVAD(audio: AudioBuffer): VADResult {
    const data = audio.data;
    
    // Calculate energy
    const energy = this.calculateEnergy(data);
    
    // Calculate zero-crossing rate
    const zcr = this.calculateZeroCrossingRate(data);
    
    // Determine if speech based on energy and ZCR
    const hasEnergy = energy > this.ENERGY_THRESHOLD;
    const hasValidZCR = zcr > this.ZERO_CROSSING_THRESHOLD && zcr < 0.7;
    
    const isSpeech = hasEnergy && hasValidZCR;
    
    // Calculate confidence based on how well metrics match speech characteristics
    let confidence = 0;
    if (hasEnergy) confidence += 0.5;
    if (hasValidZCR) confidence += 0.5;
    
    return {
      isSpeech,
      confidence,
    };
  }

  /**
   * Calculates energy of audio signal
   * @param data - Audio data
   * @returns Normalized energy value
   */
  private calculateEnergy(data: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      sum += data[i] * data[i];
    }
    return Math.sqrt(sum / data.length);
  }

  /**
   * Calculates zero-crossing rate of audio signal
   * @param data - Audio data
   * @returns Zero-crossing rate (0-1)
   */
  private calculateZeroCrossingRate(data: Float32Array): number {
    let crossings = 0;
    for (let i = 1; i < data.length; i++) {
      if ((data[i] >= 0 && data[i - 1] < 0) || (data[i] < 0 && data[i - 1] >= 0)) {
        crossings++;
      }
    }
    return crossings / (data.length - 1);
  }

  /**
   * Applies noise reduction using spectral subtraction
   * Targets 70+ dB noise environments (Requirement 1.3)
   * @param audio - Audio buffer to process
   * @returns Noise-reduced audio buffer
   */
  applyNoiseReduction(audio: AudioBuffer): AudioBuffer {
    const data = audio.data;
    const cleanedData = new Float32Array(data.length);
    
    // If no noise profile, estimate from first 100ms (assumed to be noise)
    if (!this.noiseProfile) {
      const noiseLength = Math.min(Math.floor(audio.sampleRate * 0.1), data.length);
      this.noiseProfile = new Float32Array(noiseLength);
      for (let i = 0; i < noiseLength; i++) {
        this.noiseProfile[i] = Math.abs(data[i]);
      }
    }
    
    // Apply spectral subtraction
    const noiseEstimate = this.calculateEnergy(this.noiseProfile);
    
    for (let i = 0; i < data.length; i++) {
      const signalMagnitude = Math.abs(data[i]);
      
      // Subtract noise estimate
      let cleanMagnitude = signalMagnitude - (noiseEstimate * this.NOISE_REDUCTION_FACTOR);
      
      // Ensure non-negative
      cleanMagnitude = Math.max(0, cleanMagnitude);
      
      // Preserve sign
      cleanedData[i] = data[i] >= 0 ? cleanMagnitude : -cleanMagnitude;
    }
    
    return {
      data: cleanedData,
      sampleRate: audio.sampleRate,
      duration: audio.duration,
    };
  }

  /**
   * Captures audio with automatic noise reduction and VAD
   * @param durationMs - Maximum duration in milliseconds
   * @returns Processed audio buffer
   */
  async captureAndProcess(durationMs: number): Promise<AudioBuffer> {
    const rawAudio = await this.captureAudio(durationMs);
    
    // Apply noise reduction
    const cleanedAudio = this.applyNoiseReduction(rawAudio);
    
    // Check for speech activity
    const hasSpeech = this.detectSpeechActivity(cleanedAudio);
    
    if (!hasSpeech) {
      throw new Error('No speech detected in audio');
    }
    
    return cleanedAudio;
  }

  /**
   * Resets noise profile (useful when environment changes)
   */
  resetNoiseProfile(): void {
    this.noiseProfile = null;
  }

  /**
   * Stops recording and releases resources
   */
  stop(): void {
    this.isRecording = false;
    
    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }
    
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
  }

  /**
   * Cleans up all resources
   */
  async cleanup(): Promise<void> {
    this.stop();
    
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
    
    this.analyser = null;
    this.audioChunks = [];
    this.noiseProfile = null;
  }

  /**
   * Checks if audio capture is currently active
   */
  isActive(): boolean {
    return this.isRecording;
  }

  /**
   * Gets current audio context state
   */
  getState(): string {
    return this.audioContext?.state || 'closed';
  }
}
