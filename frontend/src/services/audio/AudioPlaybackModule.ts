/**
 * AudioPlaybackModule - Handles audio playback with volume control
 * Implements TTS audio playback, adaptive volume based on ambient noise, and replay functionality
 * Requirements: 4.4, 4.5
 */

export interface PlaybackOptions {
  volume?: number; // 0-1
  playbackRate?: number; // 0.5-2.0
  loop?: boolean;
}

export interface PlaybackState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
}

export class AudioPlaybackModule {
  private audioContext: AudioContext | null = null;
  private currentSource: AudioBufferSourceNode | null = null;
  private gainNode: GainNode | null = null;
  private analyser: AnalyserNode | null = null;
  private lastPlayedAudio: AudioBuffer | null = null;
  private isPlaying = false;
  private startTime = 0;
  private pauseTime = 0;
  
  // Adaptive volume parameters
  private readonly BASE_VOLUME = 0.7;
  private readonly AMBIENT_NOISE_THRESHOLD = 60; // dB
  private readonly VOLUME_BOOST_FACTOR = 0.3; // 30% boost per 10dB above threshold
  private ambientNoiseLevel = 50; // Default ambient noise level in dB

  /**
   * Initializes audio context and nodes
   */
  async initialize(): Promise<void> {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Create gain node for volume control
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = this.BASE_VOLUME;
      
      // Create analyser for ambient noise detection
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      
      // Connect nodes
      this.gainNode.connect(this.audioContext.destination);
      
    } catch (error) {
      throw new Error(`Failed to initialize audio playback: ${error}`);
    }
  }

  /**
   * Plays audio from a blob (e.g., TTS output)
   * @param audioBlob - Audio blob to play
   * @param options - Playback options
   */
  async playAudio(audioBlob: Blob, options: PlaybackOptions = {}): Promise<void> {
    if (!this.audioContext || !this.gainNode) {
      throw new Error('Audio playback not initialized');
    }

    try {
      // Stop any currently playing audio
      this.stop();
      
      // Convert blob to array buffer
      const arrayBuffer = await audioBlob.arrayBuffer();
      
      // Decode audio data
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      
      // Store for replay functionality
      this.lastPlayedAudio = audioBuffer;
      
      // Play the audio
      await this.playAudioBuffer(audioBuffer, options);
      
    } catch (error) {
      throw new Error(`Failed to play audio: ${error}`);
    }
  }

  /**
   * Plays audio from an AudioBuffer
   * @param audioBuffer - Audio buffer to play
   * @param options - Playback options
   */
  async playAudioBuffer(audioBuffer: AudioBuffer, options: PlaybackOptions = {}): Promise<void> {
    if (!this.audioContext || !this.gainNode) {
      throw new Error('Audio playback not initialized');
    }

    // Create buffer source
    this.currentSource = this.audioContext.createBufferSource();
    this.currentSource.buffer = audioBuffer;
    
    // Set playback rate if specified
    if (options.playbackRate) {
      this.currentSource.playbackRate.value = options.playbackRate;
    }
    
    // Set loop if specified
    if (options.loop) {
      this.currentSource.loop = true;
    }
    
    // Set volume (with adaptive adjustment if not manually specified)
    if (options.volume !== undefined) {
      this.gainNode.gain.value = options.volume;
    } else {
      // Apply adaptive volume based on ambient noise
      const adaptiveVolume = this.calculateAdaptiveVolume();
      this.gainNode.gain.value = adaptiveVolume;
    }
    
    // Connect source to gain node
    this.currentSource.connect(this.gainNode);
    
    // Set up ended event
    this.currentSource.onended = () => {
      this.isPlaying = false;
    };
    
    // Start playback
    this.currentSource.start(0);
    this.isPlaying = true;
    this.startTime = this.audioContext.currentTime;
  }

  /**
   * Replays the last played audio (Requirement 4.5)
   */
  async replay(): Promise<void> {
    if (!this.lastPlayedAudio) {
      throw new Error('No audio to replay');
    }
    
    await this.playAudioBuffer(this.lastPlayedAudio);
  }

  /**
   * Stops current playback
   */
  stop(): void {
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch (error) {
        // Ignore error if already stopped
      }
      this.currentSource.disconnect();
      this.currentSource = null;
    }
    this.isPlaying = false;
  }

  /**
   * Pauses current playback
   */
  pause(): void {
    if (this.isPlaying && this.audioContext) {
      this.pauseTime = this.audioContext.currentTime - this.startTime;
      this.stop();
    }
  }

  /**
   * Resumes paused playback
   */
  async resume(): Promise<void> {
    if (this.lastPlayedAudio && this.pauseTime > 0) {
      if (!this.audioContext || !this.gainNode) {
        throw new Error('Audio playback not initialized');
      }
      
      this.currentSource = this.audioContext.createBufferSource();
      this.currentSource.buffer = this.lastPlayedAudio;
      this.currentSource.connect(this.gainNode);
      
      this.currentSource.onended = () => {
        this.isPlaying = false;
      };
      
      this.currentSource.start(0, this.pauseTime);
      this.isPlaying = true;
      this.startTime = this.audioContext.currentTime - this.pauseTime;
      this.pauseTime = 0;
    }
  }

  /**
   * Sets volume manually
   * @param volume - Volume level (0-1)
   */
  setVolume(volume: number): void {
    if (!this.gainNode) {
      throw new Error('Audio playback not initialized');
    }
    
    const clampedVolume = Math.max(0, Math.min(1, volume));
    this.gainNode.gain.value = clampedVolume;
  }

  /**
   * Gets current volume
   * @returns Current volume (0-1)
   */
  getVolume(): number {
    return this.gainNode?.gain.value || 0;
  }

  /**
   * Detects ambient noise level using microphone
   * @returns Ambient noise level in dB
   */
  async detectAmbientNoise(): Promise<number> {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      if (!this.audioContext || !this.analyser) {
        stream.getTracks().forEach(track => track.stop());
        throw new Error('Audio context not initialized');
      }
      
      // Create source from microphone
      const source = this.audioContext.createMediaStreamSource(stream);
      source.connect(this.analyser);
      
      // Measure noise level over 1 second
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      
      return new Promise((resolve) => {
        setTimeout(() => {
          this.analyser!.getByteFrequencyData(dataArray);
          
          // Calculate average amplitude
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const average = sum / dataArray.length;
          
          // Convert to dB (approximate)
          const dB = 20 * Math.log10(average / 255) + 100;
          
          // Clean up
          source.disconnect();
          stream.getTracks().forEach(track => track.stop());
          
          this.ambientNoiseLevel = dB;
          resolve(dB);
        }, 1000);
      });
      
    } catch (error) {
      // If microphone access fails, use default
      return this.ambientNoiseLevel;
    }
  }

  /**
   * Calculates adaptive volume based on ambient noise (Requirement 4.4)
   * Increases volume in noisy environments
   * @returns Adjusted volume (0-1)
   */
  calculateAdaptiveVolume(): number {
    let volume = this.BASE_VOLUME;
    
    // If ambient noise exceeds threshold, boost volume
    if (this.ambientNoiseLevel > this.AMBIENT_NOISE_THRESHOLD) {
      const excessNoise = this.ambientNoiseLevel - this.AMBIENT_NOISE_THRESHOLD;
      const boostSteps = Math.floor(excessNoise / 10);
      const boost = boostSteps * this.VOLUME_BOOST_FACTOR;
      
      volume = Math.min(1.0, this.BASE_VOLUME + boost);
    }
    
    return volume;
  }

  /**
   * Updates ambient noise level and adjusts volume if playing
   * @param noiseLevel - Noise level in dB
   */
  updateAmbientNoise(noiseLevel: number): void {
    this.ambientNoiseLevel = noiseLevel;
    
    // If currently playing, adjust volume
    if (this.isPlaying && this.gainNode) {
      const adaptiveVolume = this.calculateAdaptiveVolume();
      this.gainNode.gain.value = adaptiveVolume;
    }
  }

  /**
   * Enables automatic ambient noise monitoring
   * Periodically detects noise and adjusts volume
   * @param intervalMs - Monitoring interval in milliseconds
   * @returns Interval ID for stopping monitoring
   */
  enableAdaptiveVolume(intervalMs: number = 5000): number {
    return window.setInterval(async () => {
      const noiseLevel = await this.detectAmbientNoise();
      this.updateAmbientNoise(noiseLevel);
    }, intervalMs);
  }

  /**
   * Disables automatic ambient noise monitoring
   * @param intervalId - Interval ID from enableAdaptiveVolume
   */
  disableAdaptiveVolume(intervalId: number): void {
    clearInterval(intervalId);
  }

  /**
   * Gets current playback state
   * @returns Playback state information
   */
  getPlaybackState(): PlaybackState {
    const currentTime = this.isPlaying && this.audioContext
      ? this.audioContext.currentTime - this.startTime
      : this.pauseTime;
    
    const duration = this.lastPlayedAudio?.duration || 0;
    const volume = this.getVolume();
    
    return {
      isPlaying: this.isPlaying,
      currentTime,
      duration,
      volume,
    };
  }

  /**
   * Checks if audio is currently playing
   * @returns True if playing
   */
  isCurrentlyPlaying(): boolean {
    return this.isPlaying;
  }

  /**
   * Checks if there is audio available for replay
   * @returns True if replay is available
   */
  canReplay(): boolean {
    return this.lastPlayedAudio !== null;
  }

  /**
   * Gets ambient noise level
   * @returns Current ambient noise level in dB
   */
  getAmbientNoiseLevel(): number {
    return this.ambientNoiseLevel;
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
    
    this.gainNode = null;
    this.analyser = null;
    this.lastPlayedAudio = null;
  }
}
