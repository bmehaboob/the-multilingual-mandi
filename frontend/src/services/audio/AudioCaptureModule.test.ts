/**
 * Unit tests for AudioCaptureModule
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AudioCaptureModule, AudioBuffer } from './AudioCaptureModule';

describe('AudioCaptureModule', () => {
  let audioCaptureModule: AudioCaptureModule;

  beforeEach(() => {
    audioCaptureModule = new AudioCaptureModule();
  });

  afterEach(async () => {
    await audioCaptureModule.cleanup();
  });

  describe('Energy Calculation', () => {
    it('should calculate energy correctly for silent audio', () => {
      const silentData = new Float32Array(1000).fill(0);
      const audio: AudioBuffer = {
        data: silentData,
        sampleRate: 16000,
        duration: 1.0,
      };

      // Access private method through type assertion for testing
      const energy = (audioCaptureModule as any).calculateEnergy(audio.data);
      expect(energy).toBe(0);
    });

    it('should calculate energy correctly for audio with signal', () => {
      const signalData = new Float32Array(1000).fill(0.5);
      const audio: AudioBuffer = {
        data: signalData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const energy = (audioCaptureModule as any).calculateEnergy(audio.data);
      expect(energy).toBeGreaterThan(0);
      expect(energy).toBeCloseTo(0.5, 2);
    });
  });

  describe('Zero-Crossing Rate Calculation', () => {
    it('should calculate ZCR correctly for constant signal', () => {
      const constantData = new Float32Array(1000).fill(0.5);
      const zcr = (audioCaptureModule as any).calculateZeroCrossingRate(constantData);
      expect(zcr).toBe(0);
    });

    it('should calculate ZCR correctly for alternating signal', () => {
      const alternatingData = new Float32Array(1000);
      for (let i = 0; i < alternatingData.length; i++) {
        alternatingData[i] = i % 2 === 0 ? 0.5 : -0.5;
      }
      const zcr = (audioCaptureModule as any).calculateZeroCrossingRate(alternatingData);
      expect(zcr).toBeGreaterThan(0.9); // Should be close to 1
    });

    it('should calculate ZCR correctly for speech-like signal', () => {
      const speechLikeData = new Float32Array(1000);
      for (let i = 0; i < speechLikeData.length; i++) {
        // Simulate speech with moderate zero-crossing rate (speech typically 200-400 Hz)
        // Using higher frequency to get ZCR in speech range
        speechLikeData[i] = Math.sin(i * 1.5) * 0.5;
      }
      const zcr = (audioCaptureModule as any).calculateZeroCrossingRate(speechLikeData);
      expect(zcr).toBeGreaterThan(0.3);
      expect(zcr).toBeLessThan(0.7);
    });
  });

  describe('Voice Activity Detection', () => {
    it('should detect speech in audio with sufficient energy and valid ZCR', () => {
      const speechData = new Float32Array(1000);
      for (let i = 0; i < speechData.length; i++) {
        // Simulate speech signal with appropriate frequency for valid ZCR
        speechData[i] = Math.sin(i * 1.5) * 0.3;
      }
      const audio: AudioBuffer = {
        data: speechData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const hasSpeech = audioCaptureModule.detectSpeechActivity(audio);
      expect(hasSpeech).toBe(true);
    });

    it('should not detect speech in silent audio', () => {
      const silentData = new Float32Array(1000).fill(0);
      const audio: AudioBuffer = {
        data: silentData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const hasSpeech = audioCaptureModule.detectSpeechActivity(audio);
      expect(hasSpeech).toBe(false);
    });

    it('should not detect speech in pure noise (high ZCR, low energy)', () => {
      const noiseData = new Float32Array(1000);
      for (let i = 0; i < noiseData.length; i++) {
        noiseData[i] = (Math.random() - 0.5) * 0.01; // Low amplitude noise
      }
      const audio: AudioBuffer = {
        data: noiseData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const hasSpeech = audioCaptureModule.detectSpeechActivity(audio);
      expect(hasSpeech).toBe(false);
    });
  });

  describe('Noise Reduction', () => {
    it('should reduce noise in audio signal', () => {
      const noisyData = new Float32Array(1000);
      for (let i = 0; i < noisyData.length; i++) {
        // Signal + noise
        noisyData[i] = Math.sin(i * 0.1) * 0.5 + (Math.random() - 0.5) * 0.1;
      }
      const audio: AudioBuffer = {
        data: noisyData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const cleanedAudio = audioCaptureModule.applyNoiseReduction(audio);
      
      expect(cleanedAudio.data.length).toBe(audio.data.length);
      expect(cleanedAudio.sampleRate).toBe(audio.sampleRate);
      expect(cleanedAudio.duration).toBe(audio.duration);
      
      // Cleaned audio should have non-zero values (signal preserved)
      const hasSignal = Array.from(cleanedAudio.data).some(val => Math.abs(val) > 0.01);
      expect(hasSignal).toBe(true);
    });

    it('should handle silent audio in noise reduction', () => {
      const silentData = new Float32Array(1000).fill(0);
      const audio: AudioBuffer = {
        data: silentData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const cleanedAudio = audioCaptureModule.applyNoiseReduction(audio);
      
      expect(cleanedAudio.data.length).toBe(audio.data.length);
      // All values should remain zero or very close to zero
      const maxValue = Math.max(...Array.from(cleanedAudio.data).map(Math.abs));
      expect(maxValue).toBeLessThan(0.01);
    });

    it('should preserve signal polarity after noise reduction', () => {
      const signalData = new Float32Array(100);
      for (let i = 0; i < signalData.length; i++) {
        signalData[i] = i < 50 ? 0.5 : -0.5;
      }
      const audio: AudioBuffer = {
        data: signalData,
        sampleRate: 16000,
        duration: 1.0,
      };

      const cleanedAudio = audioCaptureModule.applyNoiseReduction(audio);
      
      // Check that positive values remain positive and negative remain negative
      for (let i = 0; i < 50; i++) {
        if (cleanedAudio.data[i] !== 0) {
          expect(cleanedAudio.data[i]).toBeGreaterThanOrEqual(0);
        }
      }
      for (let i = 50; i < 100; i++) {
        if (cleanedAudio.data[i] !== 0) {
          expect(cleanedAudio.data[i]).toBeLessThanOrEqual(0);
        }
      }
    });
  });

  describe('Noise Profile Management', () => {
    it('should reset noise profile', () => {
      const audio: AudioBuffer = {
        data: new Float32Array(1000).fill(0.1),
        sampleRate: 16000,
        duration: 1.0,
      };

      // Apply noise reduction to create noise profile
      audioCaptureModule.applyNoiseReduction(audio);
      
      // Reset noise profile
      audioCaptureModule.resetNoiseProfile();
      
      // Apply again - should create new profile
      const cleanedAudio = audioCaptureModule.applyNoiseReduction(audio);
      expect(cleanedAudio).toBeDefined();
    });
  });

  describe('State Management', () => {
    it('should report correct initial state', () => {
      expect(audioCaptureModule.isActive()).toBe(false);
      expect(audioCaptureModule.getState()).toBe('closed');
    });

    it('should stop recording', () => {
      audioCaptureModule.stop();
      expect(audioCaptureModule.isActive()).toBe(false);
    });
  });
});
