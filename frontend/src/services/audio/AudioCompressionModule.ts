/**
 * AudioCompressionModule - Handles audio compression for low bandwidth
 * Implements Opus codec compression and adaptive bitrate based on network speed
 * Requirements: 2.5, 10.1
 */

import { AudioBuffer } from './AudioCaptureModule';

export interface CompressionResult {
  compressedData: Blob;
  originalSize: number;
  compressedSize: number;
  compressionRatio: number;
  bitrate: number;
}

export interface NetworkCondition {
  speed: number; // kbps
  latency: number; // ms
  quality: 'excellent' | 'good' | 'fair' | 'poor';
}

export class AudioCompressionModule {
  private mediaRecorder: MediaRecorder | null = null;
  private currentBitrate: number = 16000; // Default 16 kbps
  
  // Bitrate thresholds based on network speed
  private readonly BITRATE_EXCELLENT = 32000; // 32 kbps for excellent connection
  private readonly BITRATE_GOOD = 24000; // 24 kbps for good connection
  private readonly BITRATE_FAIR = 16000; // 16 kbps for fair connection
  private readonly BITRATE_POOR = 12000; // 12 kbps for poor connection (2G)
  
  // Network speed thresholds (kbps)
  private readonly SPEED_EXCELLENT = 1000; // 1 Mbps+
  private readonly SPEED_GOOD = 500; // 500 kbps
  private readonly SPEED_FAIR = 200; // 200 kbps
  private readonly SPEED_POOR = 100; // 100 kbps (2G threshold)

  /**
   * Compresses audio buffer to Opus format
   * Target: 60%+ size reduction (Requirement 2.5, 10.1)
   * @param audio - Audio buffer to compress
   * @param bitrate - Target bitrate in bps (optional, uses adaptive if not specified)
   * @returns Compressed audio data
   */
  async compressAudio(
    audio: AudioBuffer,
    bitrate?: number
  ): Promise<CompressionResult> {
    const targetBitrate = bitrate || this.currentBitrate;
    
    try {
      // Convert Float32Array to WAV format first
      const wavBlob = this.audioBufferToWav(audio);
      const originalSize = wavBlob.size;
      
      // Create MediaRecorder with Opus codec
      const stream = await this.createAudioStream(audio);
      
      // Try Opus codec first, fallback to other codecs if not supported
      const mimeType = this.selectBestMimeType(targetBitrate);
      
      const compressedBlob = await this.recordWithMediaRecorder(
        stream,
        mimeType,
        targetBitrate,
        audio.duration
      );
      
      const compressedSize = compressedBlob.size;
      const compressionRatio = (1 - compressedSize / originalSize) * 100;
      
      return {
        compressedData: compressedBlob,
        originalSize,
        compressedSize,
        compressionRatio,
        bitrate: targetBitrate,
      };
    } catch (error) {
      throw new Error(`Audio compression failed: ${error}`);
    }
  }

  /**
   * Selects best available MIME type for compression
   * Prefers Opus, falls back to other formats
   * @param bitrate - Target bitrate
   * @returns MIME type string
   */
  private selectBestMimeType(bitrate: number): string {
    const opusTypes = [
      `audio/webm;codecs=opus`,
      `audio/ogg;codecs=opus`,
    ];
    
    // Try Opus formats first
    for (const type of opusTypes) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    
    // Fallback to other formats
    const fallbackTypes = [
      'audio/webm',
      'audio/ogg',
      'audio/mp4',
    ];
    
    for (const type of fallbackTypes) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    
    throw new Error('No supported audio compression format found');
  }

  /**
   * Records audio using MediaRecorder with specified codec and bitrate
   * @param stream - Audio stream
   * @param mimeType - MIME type for encoding
   * @param bitrate - Target bitrate
   * @param duration - Recording duration in seconds
   * @returns Compressed audio blob
   */
  private async recordWithMediaRecorder(
    stream: MediaStream,
    mimeType: string,
    bitrate: number,
    duration: number
  ): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const chunks: Blob[] = [];
      
      try {
        this.mediaRecorder = new MediaRecorder(stream, {
          mimeType,
          audioBitsPerSecond: bitrate,
        });
        
        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data);
          }
        };
        
        this.mediaRecorder.onstop = () => {
          const blob = new Blob(chunks, { type: mimeType });
          stream.getTracks().forEach(track => track.stop());
          resolve(blob);
        };
        
        this.mediaRecorder.onerror = (event) => {
          stream.getTracks().forEach(track => track.stop());
          reject(new Error(`MediaRecorder error: ${event}`));
        };
        
        this.mediaRecorder.start();
        
        // Stop after duration
        setTimeout(() => {
          if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
          }
        }, duration * 1000);
        
      } catch (error) {
        stream.getTracks().forEach(track => track.stop());
        reject(error);
      }
    });
  }

  /**
   * Creates an audio stream from audio buffer
   * @param audio - Audio buffer
   * @returns MediaStream
   */
  private async createAudioStream(audio: AudioBuffer): Promise<MediaStream> {
    // Create an offline audio context to generate the stream
    const offlineContext = new OfflineAudioContext(
      1,
      audio.data.length,
      audio.sampleRate
    );
    
    const buffer = offlineContext.createBuffer(1, audio.data.length, audio.sampleRate);
    const channelData = new Float32Array(audio.data);
    buffer.copyToChannel(channelData, 0);
    
    const source = offlineContext.createBufferSource();
    source.buffer = buffer;
    source.connect(offlineContext.destination);
    
    // For actual streaming, we need to use MediaStreamAudioDestinationNode
    const audioContext = new AudioContext({ sampleRate: audio.sampleRate });
    const streamDestination = audioContext.createMediaStreamDestination();
    
    const streamBuffer = audioContext.createBuffer(1, audio.data.length, audio.sampleRate);
    const streamChannelData = new Float32Array(audio.data);
    streamBuffer.copyToChannel(streamChannelData, 0);
    
    const streamSource = audioContext.createBufferSource();
    streamSource.buffer = streamBuffer;
    streamSource.connect(streamDestination);
    streamSource.start();
    
    return streamDestination.stream;
  }

  /**
   * Converts audio buffer to WAV format for size comparison
   * @param audio - Audio buffer
   * @returns WAV blob
   */
  private audioBufferToWav(audio: AudioBuffer): Blob {
    const numChannels = 1;
    const sampleRate = audio.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
    
    const bytesPerSample = bitDepth / 8;
    const blockAlign = numChannels * bytesPerSample;
    
    const dataLength = audio.data.length * bytesPerSample;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);
    
    // WAV header
    this.writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    this.writeString(view, 8, 'WAVE');
    this.writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // fmt chunk size
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true); // byte rate
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);
    this.writeString(view, 36, 'data');
    view.setUint32(40, dataLength, true);
    
    // Write audio data
    const offset = 44;
    for (let i = 0; i < audio.data.length; i++) {
      const sample = Math.max(-1, Math.min(1, audio.data[i]));
      const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(offset + i * 2, intSample, true);
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  }

  /**
   * Writes string to DataView
   * @param view - DataView
   * @param offset - Offset
   * @param string - String to write
   */
  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  /**
   * Detects current network conditions
   * Uses Network Information API if available
   * @returns Network condition information
   */
  async detectNetworkCondition(): Promise<NetworkCondition> {
    // Try to use Network Information API
    const connection = (navigator as any).connection || 
                      (navigator as any).mozConnection || 
                      (navigator as any).webkitConnection;
    
    if (connection) {
      const effectiveType = connection.effectiveType;
      const downlink = connection.downlink * 1000; // Convert to kbps
      const rtt = connection.rtt;
      
      let quality: NetworkCondition['quality'];
      let speed: number;
      
      if (effectiveType === '4g' || downlink >= this.SPEED_EXCELLENT) {
        quality = 'excellent';
        speed = downlink || this.SPEED_EXCELLENT;
      } else if (effectiveType === '3g' || downlink >= this.SPEED_GOOD) {
        quality = 'good';
        speed = downlink || this.SPEED_GOOD;
      } else if (downlink >= this.SPEED_FAIR) {
        quality = 'fair';
        speed = downlink || this.SPEED_FAIR;
      } else {
        quality = 'poor';
        speed = downlink || this.SPEED_POOR;
      }
      
      return {
        speed,
        latency: rtt || 100,
        quality,
      };
    }
    
    // Fallback: estimate based on simple timing test
    return this.estimateNetworkSpeed();
  }

  /**
   * Estimates network speed using a simple timing test
   * @returns Estimated network condition
   */
  private async estimateNetworkSpeed(): Promise<NetworkCondition> {
    try {
      const startTime = performance.now();
      
      // Try to fetch a small resource (1KB)
      const response = await fetch('/api/ping', {
        method: 'HEAD',
        cache: 'no-cache',
      });
      
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      // Estimate speed based on latency
      let quality: NetworkCondition['quality'];
      let speed: number;
      
      if (latency < 50) {
        quality = 'excellent';
        speed = this.SPEED_EXCELLENT;
      } else if (latency < 100) {
        quality = 'good';
        speed = this.SPEED_GOOD;
      } else if (latency < 200) {
        quality = 'fair';
        speed = this.SPEED_FAIR;
      } else {
        quality = 'poor';
        speed = this.SPEED_POOR;
      }
      
      return { speed, latency, quality };
      
    } catch (error) {
      // Assume poor connection if test fails
      return {
        speed: this.SPEED_POOR,
        latency: 500,
        quality: 'poor',
      };
    }
  }

  /**
   * Adjusts bitrate based on network conditions (adaptive bitrate)
   * Requirement: 2.5, 10.1
   * @param networkCondition - Current network condition
   * @returns Adjusted bitrate
   */
  adjustBitrateForNetwork(networkCondition: NetworkCondition): number {
    let bitrate: number;
    
    switch (networkCondition.quality) {
      case 'excellent':
        bitrate = this.BITRATE_EXCELLENT;
        break;
      case 'good':
        bitrate = this.BITRATE_GOOD;
        break;
      case 'fair':
        bitrate = this.BITRATE_FAIR;
        break;
      case 'poor':
        bitrate = this.BITRATE_POOR;
        break;
      default:
        bitrate = this.BITRATE_FAIR;
    }
    
    this.currentBitrate = bitrate;
    return bitrate;
  }

  /**
   * Compresses audio with adaptive bitrate based on network
   * @param audio - Audio buffer to compress
   * @returns Compression result
   */
  async compressWithAdaptiveBitrate(audio: AudioBuffer): Promise<CompressionResult> {
    const networkCondition = await this.detectNetworkCondition();
    const bitrate = this.adjustBitrateForNetwork(networkCondition);
    
    return this.compressAudio(audio, bitrate);
  }

  /**
   * Gets current bitrate setting
   * @returns Current bitrate in bps
   */
  getCurrentBitrate(): number {
    return this.currentBitrate;
  }

  /**
   * Sets bitrate manually
   * @param bitrate - Bitrate in bps
   */
  setBitrate(bitrate: number): void {
    this.currentBitrate = bitrate;
  }

  /**
   * Cleans up resources
   */
  cleanup(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.mediaRecorder = null;
  }
}
