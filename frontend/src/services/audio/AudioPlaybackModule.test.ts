/**
 * Unit tests for AudioPlaybackModule
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AudioPlaybackModule } from './AudioPlaybackModule';

describe('AudioPlaybackModule', () => {
  let playbackModule: AudioPlaybackModule;

  beforeEach(async () => {
    playbackModule = new AudioPlaybackModule();
    await playbackModule.initialize();
  });

  afterEach(async () => {
    await playbackModule.cleanup();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      const module = new AudioPlaybackModule();
      await module.initialize();
      
      expect(module.getVolume()).toBeGreaterThan(0);
      await module.cleanup();
    });
  });

  describe('Volume Control', () => {
    it('should set volume within valid range', () => {
      playbackModule.setVolume(0.5);
      expect(playbackModule.getVolume()).toBe(0.5);
    });

    it('should clamp volume to maximum 1.0', () => {
      playbackModule.setVolume(1.5);
      expect(playbackModule.getVolume()).toBe(1.0);
    });

    it('should clamp volume to minimum 0.0', () => {
      playbackModule.setVolume(-0.5);
      expect(playbackModule.getVolume()).toBe(0.0);
    });

    it('should have default base volume', () => {
      const volume = playbackModule.getVolume();
      expect(volume).toBeGreaterThan(0);
      expect(volume).toBeLessThanOrEqual(1);
    });
  });

  describe('Adaptive Volume', () => {
    it('should calculate base volume for low ambient noise', () => {
      playbackModule.updateAmbientNoise(50); // Below threshold
      const volume = playbackModule.calculateAdaptiveVolume();
      
      expect(volume).toBe(0.7); // Base volume
    });

    it('should boost volume for high ambient noise', () => {
      playbackModule.updateAmbientNoise(70); // 10dB above threshold
      const volume = playbackModule.calculateAdaptiveVolume();
      
      expect(volume).toBeGreaterThan(0.7); // Should be boosted
      expect(volume).toBeLessThanOrEqual(1.0);
    });

    it('should boost volume proportionally to noise level', () => {
      playbackModule.updateAmbientNoise(70); // 10dB above threshold
      const volume1 = playbackModule.calculateAdaptiveVolume();
      
      playbackModule.updateAmbientNoise(75); // 15dB above threshold
      const volume2 = playbackModule.calculateAdaptiveVolume();
      
      // Both should be boosted, and volume2 should be >= volume1
      expect(volume1).toBeGreaterThan(0.7);
      expect(volume2).toBeGreaterThanOrEqual(volume1);
    });

    it('should cap volume at 1.0 even with very high noise', () => {
      playbackModule.updateAmbientNoise(120); // Very high noise
      const volume = playbackModule.calculateAdaptiveVolume();
      
      expect(volume).toBeLessThanOrEqual(1.0);
    });

    it('should update ambient noise level', () => {
      playbackModule.updateAmbientNoise(75);
      expect(playbackModule.getAmbientNoiseLevel()).toBe(75);
    });
  });

  describe('Playback State', () => {
    it('should report not playing initially', () => {
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
    });

    it('should report playback state', () => {
      const state = playbackModule.getPlaybackState();
      
      expect(state).toHaveProperty('isPlaying');
      expect(state).toHaveProperty('currentTime');
      expect(state).toHaveProperty('duration');
      expect(state).toHaveProperty('volume');
      expect(state.isPlaying).toBe(false);
    });

    it('should report no replay available initially', () => {
      expect(playbackModule.canReplay()).toBe(false);
    });
  });

  describe('Stop Functionality', () => {
    it('should stop playback', () => {
      playbackModule.stop();
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
    });

    it('should handle stop when not playing', () => {
      playbackModule.stop();
      playbackModule.stop(); // Should not throw
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
    });
  });

  describe('Pause and Resume', () => {
    it('should pause playback', () => {
      playbackModule.pause();
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
    });

    it('should handle pause when not playing', () => {
      playbackModule.pause(); // Should not throw
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
    });
  });

  describe('Ambient Noise Detection', () => {
    it('should detect ambient noise level', async () => {
      const noiseLevel = await playbackModule.detectAmbientNoise();
      
      expect(typeof noiseLevel).toBe('number');
      expect(noiseLevel).toBeGreaterThanOrEqual(0);
    });

    it('should handle microphone access failure gracefully', async () => {
      // Mock getUserMedia to fail
      const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(
        new Error('Permission denied')
      );
      
      const noiseLevel = await playbackModule.detectAmbientNoise();
      
      // Should return default value
      expect(typeof noiseLevel).toBe('number');
      
      // Restore
      navigator.mediaDevices.getUserMedia = originalGetUserMedia;
    });
  });

  describe('Adaptive Volume Monitoring', () => {
    it('should enable adaptive volume monitoring', () => {
      const intervalId = playbackModule.enableAdaptiveVolume(1000);
      
      // In test environment, setInterval might return different types
      expect(intervalId).toBeDefined();
      
      playbackModule.disableAdaptiveVolume(intervalId);
    });

    it('should disable adaptive volume monitoring', () => {
      const intervalId = playbackModule.enableAdaptiveVolume(1000);
      playbackModule.disableAdaptiveVolume(intervalId);
      
      // Should not throw
      expect(true).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should throw error when playing without initialization', async () => {
      const uninitializedModule = new AudioPlaybackModule();
      const audioBlob = new Blob(['test'], { type: 'audio/wav' });
      
      await expect(uninitializedModule.playAudio(audioBlob)).rejects.toThrow();
    });

    it('should throw error when setting volume without initialization', () => {
      const uninitializedModule = new AudioPlaybackModule();
      
      expect(() => uninitializedModule.setVolume(0.5)).toThrow();
    });

    it('should throw error when replaying without previous audio', async () => {
      await expect(playbackModule.replay()).rejects.toThrow('No audio to replay');
    });
  });

  describe('Cleanup', () => {
    it('should cleanup resources', async () => {
      await playbackModule.cleanup();
      
      expect(playbackModule.isCurrentlyPlaying()).toBe(false);
      expect(playbackModule.canReplay()).toBe(false);
    });

    it('should handle multiple cleanup calls', async () => {
      await playbackModule.cleanup();
      await playbackModule.cleanup(); // Should not throw
      
      expect(true).toBe(true);
    });
  });
});
