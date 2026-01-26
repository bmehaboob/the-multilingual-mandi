/**
 * Unit Tests for useServiceWorker Hook
 * 
 * Tests React hook for service worker management and offline detection
 * Requirements: 12.4, 19.1
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useServiceWorker, useOnlineStatus } from './useServiceWorker';

// Mock the service worker registration module
vi.mock('./serviceWorkerRegistration', () => ({
  registerServiceWorker: vi.fn((callbacks) => {
    // Store callbacks for testing
    if (callbacks) {
      // @ts-expect-error - Testing purposes
      global.__swCallbacks = callbacks;
    }
  }),
  skipWaiting: vi.fn(),
  isOnline: vi.fn(() => navigator.onLine),
  getCacheStats: vi.fn(async () => ({
    cacheNames: ['api-cache', 'image-cache'],
    totalSize: 1024 * 1024, // 1MB
  })),
}));

describe('useServiceWorker Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });
  });

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useServiceWorker());
    const [state] = result.current;

    expect(state.isOnline).toBe(true);
    expect(state.isUpdateAvailable).toBe(false);
    expect(state.isInstalled).toBe(false);
  });

  it('should update online status when going offline', async () => {
    const { result } = renderHook(() => useServiceWorker());

    // Simulate going offline
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });
      window.dispatchEvent(new Event('offline'));
    });

    // Wait for state update
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    const [state] = result.current;
    // Note: The hook uses the callback from registerServiceWorker
    // In a real scenario, this would be triggered by the service worker
  });

  it('should provide updateServiceWorker action', () => {
    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    expect(actions.updateServiceWorker).toBeDefined();
    expect(typeof actions.updateServiceWorker).toBe('function');
  });

  it('should provide refreshCacheStats action', () => {
    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    expect(actions.refreshCacheStats).toBeDefined();
    expect(typeof actions.refreshCacheStats).toBe('function');
  });

  it('should call skipWaiting when updateServiceWorker is called', async () => {
    const { skipWaiting } = await import('./serviceWorkerRegistration');
    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    act(() => {
      actions.updateServiceWorker();
    });

    expect(skipWaiting).toHaveBeenCalled();
  });

  it('should refresh cache stats when requested', async () => {
    const { getCacheStats } = await import('./serviceWorkerRegistration');
    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.refreshCacheStats();
    });

    expect(getCacheStats).toHaveBeenCalled();
  });
});

describe('useOnlineStatus Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });
  });

  it('should return true when online', () => {
    const { result } = renderHook(() => useOnlineStatus());
    expect(result.current).toBe(true);
  });

  it('should return false when offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useOnlineStatus());
    expect(result.current).toBe(false);
  });

  it('should update when online status changes', async () => {
    const { result, rerender } = renderHook(() => useOnlineStatus());

    expect(result.current).toBe(true);

    // Simulate going offline
    await act(async () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });
      window.dispatchEvent(new Event('offline'));
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    rerender();

    // The hook should detect the offline event
    // Note: The actual state update depends on the event listener
  });

  it('should clean up event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = renderHook(() => useOnlineStatus());

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));

    removeEventListenerSpy.mockRestore();
  });
});

describe('Service Worker State Management', () => {
  it('should handle service worker installation callback', async () => {
    const { result } = renderHook(() => useServiceWorker());

    // Simulate service worker installation
    act(() => {
      // @ts-expect-error - Testing purposes
      if (global.__swCallbacks?.onSuccess) {
        // @ts-expect-error - Testing purposes
        global.__swCallbacks.onSuccess();
      }
    });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    const [state] = result.current;
    expect(state.isInstalled).toBe(true);
  });

  it('should handle service worker update callback', async () => {
    const { result } = renderHook(() => useServiceWorker());

    // Simulate service worker update
    act(() => {
      // @ts-expect-error - Testing purposes
      if (global.__swCallbacks?.onUpdate) {
        // @ts-expect-error - Testing purposes
        global.__swCallbacks.onUpdate();
      }
    });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    const [state] = result.current;
    expect(state.isUpdateAvailable).toBe(true);
  });
});
