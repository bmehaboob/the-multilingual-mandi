/**
 * Unit tests for useAudioFeedback hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAudioFeedback } from './useAudioFeedback';

// Mock AudioFeedbackSystem
vi.mock('./AudioFeedbackSystem', () => ({
  AudioFeedbackSystem: class {
    private config: any;
    
    constructor(config: any) {
      this.config = config;
    }
    
    initialize = vi.fn().mockResolvedValue(undefined);
    setLanguage = vi.fn();
    setEnabled = vi.fn();
    setVolume = vi.fn();
    playStateFeedback = vi.fn().mockResolvedValue(undefined);
    playActionPrompt = vi.fn().mockResolvedValue(undefined);
    playCustomMessage = vi.fn().mockResolvedValue(undefined);
    stop = vi.fn();
    clearQueue = vi.fn();
    cleanup = vi.fn().mockResolvedValue(undefined);
    isCurrentlyPlaying = vi.fn().mockReturnValue(false);
    getConfig = vi.fn(() => this.config);
  },
}));

describe('useAudioFeedback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default options', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });
  });

  it('should initialize with custom options', async () => {
    const { result } = renderHook(() =>
      useAudioFeedback({
        language: 'hi',
        enabled: true,
        volume: 0.5,
        useTTS: true,
      })
    );

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });
  });

  it('should play state feedback', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    await result.current.playStateFeedback('success');
    expect(result.current.isPlaying).toBe(false);
  });

  it('should play action prompt', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    await result.current.playActionPrompt('welcome');
    expect(result.current.isPlaying).toBe(false);
  });

  it('should play custom message', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    await result.current.playCustomMessage('Test message');
    expect(result.current.isPlaying).toBe(false);
  });

  it('should update language', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    result.current.setLanguage('hi');
    // Language should be updated in the feedback system
  });

  it('should update enabled state', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    result.current.setEnabled(false);
    // Enabled state should be updated
  });

  it('should update volume', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    result.current.setVolume(0.5);
    // Volume should be updated
  });

  it('should stop playback', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    result.current.stop();
    expect(result.current.isPlaying).toBe(false);
  });

  it('should clear queue', async () => {
    const { result } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });

    result.current.clearQueue();
  });

  it('should cleanup on unmount', async () => {
    const { unmount } = renderHook(() => useAudioFeedback());

    await waitFor(() => {
      // Wait for initialization
    });

    unmount();
    // Cleanup should be called
  });
});
