/**
 * Unit tests for AudioFeedbackSystem
 * 
 * Tests audio feedback for system states and voice prompts
 * Requirements: 11.1, 11.4
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AudioFeedbackSystem, AudioFeedbackConfig, SystemState, ActionPrompt } from './AudioFeedbackSystem';

// Mock AudioContext
class MockAudioContext {
  destination = {};
  currentTime = 0;
  
  createOscillator() {
    const oscillator = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn((time?: number) => {
        // Trigger onended immediately
        setTimeout(() => {
          if (oscillator.onended) {
            oscillator.onended();
          }
        }, 0);
      }),
      frequency: { value: 0 },
      type: 'sine' as OscillatorType,
      onended: null as (() => void) | null,
    };
    return oscillator;
  }
  
  createGain() {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      gain: {
        value: 0,
        setValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
      },
    };
  }
  
  close() {
    return Promise.resolve();
  }
}

// Mock AudioPlaybackModule
vi.mock('./AudioPlaybackModule', () => ({
  AudioPlaybackModule: class {
    initialize = vi.fn().mockResolvedValue(undefined);
    setVolume = vi.fn();
    stop = vi.fn();
    cleanup = vi.fn().mockResolvedValue(undefined);
  },
}));

describe('AudioFeedbackSystem', () => {
  let feedbackSystem: AudioFeedbackSystem;
  let config: AudioFeedbackConfig;

  beforeEach(() => {
    // Mock AudioContext on window
    (window as any).AudioContext = MockAudioContext;
    (window as any).webkitAudioContext = MockAudioContext;

    // Mock speechSynthesis
    (window as any).speechSynthesis = {
      speak: vi.fn((utterance: any) => {
        // Simulate async completion
        setTimeout(() => {
          if (utterance.onend) utterance.onend();
        }, 0);
      }),
      cancel: vi.fn(),
    };
    
    (window as any).SpeechSynthesisUtterance = class {
      text: string;
      lang = '';
      rate = 1;
      volume = 1;
      onend: (() => void) | null = null;
      onerror: ((error: any) => void) | null = null;
      
      constructor(text: string) {
        this.text = text;
      }
    };

    config = {
      language: 'en',
      enabled: true,
      volume: 0.7,
      useTTS: true,
    };

    feedbackSystem = new AudioFeedbackSystem(config);
  });

  afterEach(async () => {
    await feedbackSystem.cleanup();
    vi.clearAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      await expect(feedbackSystem.initialize()).resolves.not.toThrow();
    });
  });

  describe('Configuration', () => {
    it('should set language', async () => {
      await feedbackSystem.initialize();
      feedbackSystem.setLanguage('hi');
      expect(feedbackSystem.getConfig().language).toBe('hi');
    });

    it('should enable/disable feedback', async () => {
      await feedbackSystem.initialize();
      feedbackSystem.setEnabled(false);
      expect(feedbackSystem.getConfig().enabled).toBe(false);
      
      feedbackSystem.setEnabled(true);
      expect(feedbackSystem.getConfig().enabled).toBe(true);
    });

    it('should set volume', async () => {
      await feedbackSystem.initialize();
      feedbackSystem.setVolume(0.5);
      expect(feedbackSystem.getConfig().volume).toBe(0.5);
    });

    it('should clamp volume between 0 and 1', async () => {
      await feedbackSystem.initialize();
      
      feedbackSystem.setVolume(1.5);
      expect(feedbackSystem.getConfig().volume).toBe(1);
      
      feedbackSystem.setVolume(-0.5);
      expect(feedbackSystem.getConfig().volume).toBe(0);
    });
  });

  describe('State Feedback', () => {
    it('should play state feedback for loading', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.playStateFeedback('loading')).resolves.not.toThrow();
    });

    it('should play state feedback for success', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.playStateFeedback('success')).resolves.not.toThrow();
    });

    it('should play state feedback for error', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.playStateFeedback('error')).resolves.not.toThrow();
    });

    it('should play state feedback for all system states', async () => {
      await feedbackSystem.initialize();
      
      const states: SystemState[] = [
        'loading', 'success', 'error', 'warning', 'info',
        'processing', 'connecting', 'offline', 'online'
      ];

      for (const state of states) {
        await expect(feedbackSystem.playStateFeedback(state)).resolves.not.toThrow();
      }
    });

    it('should not play feedback when disabled', async () => {
      await feedbackSystem.initialize();
      feedbackSystem.setEnabled(false);
      
      await feedbackSystem.playStateFeedback('success');
      
      // Should not throw and should complete immediately
      expect(feedbackSystem.isCurrentlyPlaying()).toBe(false);
    });

    it('should play custom message for state feedback', async () => {
      await feedbackSystem.initialize();
      const customMessage = 'Custom loading message';
      
      await expect(
        feedbackSystem.playStateFeedback('loading', customMessage)
      ).resolves.not.toThrow();
    });
  });

  describe('Action Prompts', () => {
    it('should play action prompt for start_conversation', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.playActionPrompt('start_conversation')).resolves.not.toThrow();
    });

    it('should play action prompt for check_price', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.playActionPrompt('check_price')).resolves.not.toThrow();
    });

    it('should play action prompts for all actions', async () => {
      await feedbackSystem.initialize();
      
      const actions: ActionPrompt[] = [
        'start_conversation', 'check_price', 'request_negotiation',
        'end_conversation', 'switch_conversation', 'view_history',
        'replay_message', 'confirm_action', 'cancel_action',
        'welcome', 'goodbye'
      ];

      for (const action of actions) {
        await expect(feedbackSystem.playActionPrompt(action)).resolves.not.toThrow();
      }
    });

    it('should play custom message for action prompt', async () => {
      await feedbackSystem.initialize();
      const customMessage = 'Custom action message';
      
      await expect(
        feedbackSystem.playActionPrompt('start_conversation', customMessage)
      ).resolves.not.toThrow();
    });
  });

  describe('Multilingual Support', () => {
    it('should support Hindi language', async () => {
      feedbackSystem.setLanguage('hi');
      await feedbackSystem.initialize();
      
      await expect(feedbackSystem.playStateFeedback('success')).resolves.not.toThrow();
      await expect(feedbackSystem.playActionPrompt('welcome')).resolves.not.toThrow();
    });

    it('should support Telugu language', async () => {
      feedbackSystem.setLanguage('te');
      await feedbackSystem.initialize();
      
      await expect(feedbackSystem.playStateFeedback('loading')).resolves.not.toThrow();
      await expect(feedbackSystem.playActionPrompt('check_price')).resolves.not.toThrow();
    });

    it('should support Tamil language', async () => {
      feedbackSystem.setLanguage('ta');
      await feedbackSystem.initialize();
      
      await expect(feedbackSystem.playStateFeedback('error')).resolves.not.toThrow();
      await expect(feedbackSystem.playActionPrompt('goodbye')).resolves.not.toThrow();
    });

    it('should fallback to English for unsupported language', async () => {
      feedbackSystem.setLanguage('unsupported');
      await feedbackSystem.initialize();
      
      await expect(feedbackSystem.playStateFeedback('success')).resolves.not.toThrow();
    });
  });

  describe('Queue Management', () => {
    it('should queue feedback when already playing', async () => {
      await feedbackSystem.initialize();
      
      // Start playing
      const promise1 = feedbackSystem.playStateFeedback('loading');
      
      // Queue another feedback
      const promise2 = feedbackSystem.playStateFeedback('success');
      
      await Promise.all([promise1, promise2]);
    });

    it('should clear queue', async () => {
      await feedbackSystem.initialize();
      
      feedbackSystem.clearQueue();
      expect(feedbackSystem.isCurrentlyPlaying()).toBe(false);
    });
  });

  describe('Custom Messages', () => {
    it('should play custom message', async () => {
      await feedbackSystem.initialize();
      const message = 'This is a custom message';
      
      await expect(feedbackSystem.playCustomMessage(message)).resolves.not.toThrow();
    });
  });

  describe('Control Methods', () => {
    it('should stop playing feedback', async () => {
      await feedbackSystem.initialize();
      
      feedbackSystem.stop();
      expect(feedbackSystem.isCurrentlyPlaying()).toBe(false);
    });

    it('should report playing status', async () => {
      await feedbackSystem.initialize();
      
      expect(feedbackSystem.isCurrentlyPlaying()).toBe(false);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup resources', async () => {
      await feedbackSystem.initialize();
      await expect(feedbackSystem.cleanup()).resolves.not.toThrow();
    });
  });
});
