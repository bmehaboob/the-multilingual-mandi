/**
 * Tests for Offline Notification Hook
 * 
 * Requirements: 12.4
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useOfflineNotification, useOfflineNotificationWithStatus } from './useOfflineNotification';
import * as useServiceWorkerModule from './useServiceWorker';
import { AudioFeedbackSystem } from './audio/AudioFeedbackSystem';

// Mock the useServiceWorker module
vi.mock('./useServiceWorker', () => ({
  useOnlineStatus: vi.fn(),
}));

// Mock AudioFeedbackSystem
vi.mock('./audio/AudioFeedbackSystem', () => {
  const mockPlayStateFeedback = vi.fn().mockResolvedValue(undefined);
  const mockSetLanguage = vi.fn();
  const mockSetVolume = vi.fn();
  const mockCleanup = vi.fn().mockResolvedValue(undefined);
  const mockInitialize = vi.fn().mockResolvedValue(undefined);

  return {
    AudioFeedbackSystem: vi.fn().mockImplementation(() => ({
      initialize: mockInitialize,
      playStateFeedback: mockPlayStateFeedback,
      setLanguage: mockSetLanguage,
      setVolume: mockSetVolume,
      cleanup: mockCleanup,
    })),
  };
});

describe('useOfflineNotification', () => {
  let mockUseOnlineStatus: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseOnlineStatus = vi.mocked(useServiceWorkerModule.useOnlineStatus);
    
    // Default to online
    mockUseOnlineStatus.mockReturnValue(true);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Initialization', () => {
    it('should initialize AudioFeedbackSystem when enabled', async () => {
      const { result } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
          volume: 0.7,
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalledWith({
          language: 'en',
          enabled: true,
          volume: 0.7,
          useTTS: true,
        });
      });
    });

    it('should not initialize AudioFeedbackSystem when disabled', async () => {
      const { result } = renderHook(() =>
        useOfflineNotification({
          enabled: false,
          language: 'en',
        })
      );

      // Wait a bit to ensure initialization doesn't happen
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(AudioFeedbackSystem).not.toHaveBeenCalled();
    });

    it('should use default volume if not provided', async () => {
      const { result } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalledWith({
          language: 'en',
          enabled: true,
          volume: 0.7,
          useTTS: true,
        });
      });
    });

    it('should handle initialization errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      // Mock initialization to fail
      const mockInitialize = vi.fn().mockRejectedValue(new Error('Init failed'));
      vi.mocked(AudioFeedbackSystem).mockImplementationOnce(() => ({
        initialize: mockInitialize,
        playStateFeedback: vi.fn(),
        setLanguage: vi.fn(),
        setVolume: vi.fn(),
        cleanup: vi.fn(),
      } as any));

      const { result } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Failed to initialize audio feedback for offline notifications:',
          expect.any(Error)
        );
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Network Status Change Detection', () => {
    it('should not announce initial online status', async () => {
      mockUseOnlineStatus.mockReturnValue(true);

      const { result } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      // Get the mock instance
      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Should not call playStateFeedback on initial render
      expect(mockInstance.playStateFeedback).not.toHaveBeenCalled();
    });

    it('should announce when going offline', async () => {
      // Start online
      mockUseOnlineStatus.mockReturnValue(true);

      const { rerender } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Change to offline
      mockUseOnlineStatus.mockReturnValue(false);
      rerender();

      await waitFor(() => {
        expect(mockInstance.playStateFeedback).toHaveBeenCalledWith('offline');
      });
    });

    it('should announce when going online', async () => {
      // Start offline
      mockUseOnlineStatus.mockReturnValue(false);

      const { rerender } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Change to online
      mockUseOnlineStatus.mockReturnValue(true);
      rerender();

      await waitFor(() => {
        expect(mockInstance.playStateFeedback).toHaveBeenCalledWith('online');
      });
    });

    it('should not announce if status has not changed', async () => {
      mockUseOnlineStatus.mockReturnValue(true);

      const { rerender } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Rerender without changing status
      rerender();
      rerender();

      // Should not call playStateFeedback
      expect(mockInstance.playStateFeedback).not.toHaveBeenCalled();
    });

    it('should not announce when disabled', async () => {
      mockUseOnlineStatus.mockReturnValue(true);

      const { rerender } = renderHook(() =>
        useOfflineNotification({
          enabled: false,
          language: 'en',
        })
      );

      // Change to offline
      mockUseOnlineStatus.mockReturnValue(false);
      rerender();

      // Should not initialize AudioFeedbackSystem at all
      expect(AudioFeedbackSystem).not.toHaveBeenCalled();
    });
  });

  describe('Language Updates', () => {
    it('should update language when config changes', async () => {
      const { rerender } = renderHook(
        ({ language }) =>
          useOfflineNotification({
            enabled: true,
            language,
          }),
        { initialProps: { language: 'en' } }
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Wait for initialization to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Change language
      rerender({ language: 'hi' });

      await waitFor(() => {
        expect(mockInstance.setLanguage).toHaveBeenCalledWith('hi');
      }, { timeout: 2000 });
    });
  });

  describe('Volume Updates', () => {
    it('should update volume when config changes', async () => {
      const { rerender } = renderHook(
        ({ volume }) =>
          useOfflineNotification({
            enabled: true,
            language: 'en',
            volume,
          }),
        { initialProps: { volume: 0.5 } }
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Wait for initialization to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Change volume
      rerender({ volume: 0.9 });

      await waitFor(() => {
        expect(mockInstance.setVolume).toHaveBeenCalledWith(0.9);
      }, { timeout: 2000 });
    });

    it('should not update volume if undefined', async () => {
      const { rerender } = renderHook(
        ({ volume }) =>
          useOfflineNotification({
            enabled: true,
            language: 'en',
            volume,
          }),
        { initialProps: { volume: undefined } }
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Rerender with undefined volume
      rerender({ volume: undefined });

      // Should not call setVolume
      expect(mockInstance.setVolume).not.toHaveBeenCalled();
    });
  });

  describe('Cleanup', () => {
    it('should cleanup AudioFeedbackSystem on unmount', async () => {
      const { unmount } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      unmount();

      await waitFor(() => {
        expect(mockInstance.cleanup).toHaveBeenCalled();
      });
    });

    it('should not cleanup if not initialized', async () => {
      const { unmount } = renderHook(() =>
        useOfflineNotification({
          enabled: false,
          language: 'en',
        })
      );

      // Unmount immediately
      unmount();

      // Should not have created AudioFeedbackSystem
      expect(AudioFeedbackSystem).not.toHaveBeenCalled();
    });
  });

  describe('Multiple Status Changes', () => {
    it('should handle multiple online/offline transitions', async () => {
      mockUseOnlineStatus.mockReturnValue(true);

      const { rerender } = renderHook(() =>
        useOfflineNotification({
          enabled: true,
          language: 'en',
        })
      );

      await waitFor(() => {
        expect(AudioFeedbackSystem).toHaveBeenCalled();
      });

      const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

      // Go offline
      mockUseOnlineStatus.mockReturnValue(false);
      rerender();

      await waitFor(() => {
        expect(mockInstance.playStateFeedback).toHaveBeenCalledWith('offline');
      });

      // Go online
      mockUseOnlineStatus.mockReturnValue(true);
      rerender();

      await waitFor(() => {
        expect(mockInstance.playStateFeedback).toHaveBeenCalledWith('online');
      });

      // Go offline again
      mockUseOnlineStatus.mockReturnValue(false);
      rerender();

      await waitFor(() => {
        expect(mockInstance.playStateFeedback).toHaveBeenCalledTimes(3);
        expect(mockInstance.playStateFeedback).toHaveBeenNthCalledWith(3, 'offline');
      });
    });
  });
});

describe('useOfflineNotificationWithStatus', () => {
  let mockUseOnlineStatus: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseOnlineStatus = vi.mocked(useServiceWorkerModule.useOnlineStatus);
  });

  it('should return online status', async () => {
    mockUseOnlineStatus.mockReturnValue(true);

    const { result } = renderHook(() =>
      useOfflineNotificationWithStatus({
        enabled: true,
        language: 'en',
      })
    );

    expect(result.current).toBe(true);
  });

  it('should return offline status', async () => {
    mockUseOnlineStatus.mockReturnValue(false);

    const { result } = renderHook(() =>
      useOfflineNotificationWithStatus({
        enabled: true,
        language: 'en',
      })
    );

    expect(result.current).toBe(false);
  });

  it('should update status when network changes', async () => {
    mockUseOnlineStatus.mockReturnValue(true);

    const { result, rerender } = renderHook(() =>
      useOfflineNotificationWithStatus({
        enabled: true,
        language: 'en',
      })
    );

    expect(result.current).toBe(true);

    // Change to offline
    mockUseOnlineStatus.mockReturnValue(false);
    rerender();

    expect(result.current).toBe(false);
  });

  it('should provide voice notifications', async () => {
    mockUseOnlineStatus.mockReturnValue(true);

    const { rerender } = renderHook(() =>
      useOfflineNotificationWithStatus({
        enabled: true,
        language: 'en',
      })
    );

    await waitFor(() => {
      expect(AudioFeedbackSystem).toHaveBeenCalled();
    });

    const mockInstance = vi.mocked(AudioFeedbackSystem).mock.results[0].value;

    // Change to offline
    mockUseOnlineStatus.mockReturnValue(false);
    rerender();

    await waitFor(() => {
      expect(mockInstance.playStateFeedback).toHaveBeenCalledWith('offline');
    });
  });
});
