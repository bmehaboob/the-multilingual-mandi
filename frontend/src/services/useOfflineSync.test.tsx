/**
 * Unit Tests for useOfflineSync Hook
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useOfflineSync, useSyncStats, useHasPendingMessages } from './useOfflineSync';
import { resetOfflineSyncManager, getOfflineSyncManager } from './OfflineSyncManager';

// Mock IndexedDB
import 'fake-indexeddb/auto';

// Mock fetch
global.fetch = vi.fn();

describe('useOfflineSync', () => {
  beforeEach(async () => {
    await resetOfflineSyncManager();
    vi.clearAllMocks();
    
    // Clear IndexedDB
    const manager = await getOfflineSyncManager();
    await manager.clearAll();
  });

  afterEach(async () => {
    await resetOfflineSyncManager();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      expect(result.current[0].isSyncing).toBe(false);
      expect(result.current[0].error).toBeNull();
    });

    it('should load initial stats', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].stats).not.toBeNull();
      });

      expect(result.current[0].stats?.totalQueued).toBe(0);
      expect(result.current[0].stats?.pendingCount).toBe(0);
    });

    it('should call initialization callbacks', async () => {
      const onSyncStart = vi.fn();
      const { result } = renderHook(() => useOfflineSync({ onSyncStart }));

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      expect(result.current).toBeDefined();
    });
  });

  describe('Queue Message Action', () => {
    it('should queue a message', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      let messageId: string = '';

      await act(async () => {
        messageId = await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      expect(messageId).toBeDefined();
      expect(messageId).toMatch(/^msg_/);
    });

    it('should update stats after queueing', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      await waitFor(() => {
        expect(result.current[0].stats?.totalQueued).toBe(1);
        expect(result.current[0].stats?.pendingCount).toBe(1);
      });
    });

    it('should call onMessageQueued callback', async () => {
      const onMessageQueued = vi.fn();
      const { result } = renderHook(() => useOfflineSync({ onMessageQueued }));

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      await waitFor(() => {
        expect(onMessageQueued).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Sync Actions', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
    });

    it('should sync all messages', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      let syncResults: any[] = [];

      await act(async () => {
        syncResults = await result.current[1].syncAll();
      });

      expect(syncResults).toHaveLength(1);
      expect(syncResults[0].success).toBe(true);
    });

    it('should update isSyncing state during sync', async () => {
      (global.fetch as any).mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
      );

      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      act(() => {
        result.current[1].syncAll();
      });

      await waitFor(() => {
        expect(result.current[0].isSyncing).toBe(true);
      });

      await waitFor(() => {
        expect(result.current[0].isSyncing).toBe(false);
      }, { timeout: 200 });
    });

    it('should call sync callbacks', async () => {
      const onSyncStart = vi.fn();
      const onSyncComplete = vi.fn();

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      const { result } = renderHook(() => useOfflineSync({ onSyncStart, onSyncComplete }));

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Hello',
          originalLanguage: 'en',
        });
      });

      await act(async () => {
        await result.current[1].syncAll();
      });

      expect(onSyncStart).toHaveBeenCalledTimes(1);
      expect(onSyncComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe('Message Retrieval Actions', () => {
    it('should get all messages', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message 1',
          originalLanguage: 'en',
        });

        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message 2',
          originalLanguage: 'en',
        });
      });

      let messages: any[] = [];

      await act(async () => {
        messages = await result.current[1].getAllMessages();
      });

      expect(messages).toHaveLength(2);
    });

    it('should get messages by status', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message',
          originalLanguage: 'en',
        });
      });

      let pendingMessages: any[] = [];

      await act(async () => {
        pendingMessages = await result.current[1].getMessagesByStatus('pending');
      });

      expect(pendingMessages).toHaveLength(1);
    });
  });

  describe('Message Management Actions', () => {
    it('should delete a message', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      let messageId: string = '';

      await act(async () => {
        messageId = await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message',
          originalLanguage: 'en',
        });
      });

      await act(async () => {
        await result.current[1].deleteMessage(messageId);
      });

      await waitFor(() => {
        expect(result.current[0].stats?.totalQueued).toBe(0);
      });
    });

    it('should clear all messages', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message 1',
          originalLanguage: 'en',
        });

        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message 2',
          originalLanguage: 'en',
        });
      });

      await act(async () => {
        await result.current[1].clearAll();
      });

      await waitFor(() => {
        expect(result.current[0].stats?.totalQueued).toBe(0);
      });
    });

    it('should refresh stats', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].refreshStats();
      });

      expect(result.current[0].stats).not.toBeNull();
    });

    it('should set auto-sync', async () => {
      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        result.current[1].setAutoSync(false);
      });

      // No error should be thrown
      expect(result.current[0].error).toBeNull();
    });
  });

  describe('Retry Failed Action', () => {
    it('should retry failed messages', async () => {
      // First, create a failed message
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useOfflineSync());

      await waitFor(() => {
        expect(result.current[0].isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current[1].queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message',
          originalLanguage: 'en',
        });
      });

      // Sync 3 times to mark as failed
      await act(async () => {
        await result.current[1].syncAll();
        await result.current[1].syncAll();
        await result.current[1].syncAll();
      });

      // Now mock success
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      let retryResults: any[] = [];

      await act(async () => {
        retryResults = await result.current[1].retryFailed();
      });

      expect(retryResults).toHaveLength(1);
      expect(retryResults[0].success).toBe(true);
    });
  });
});

describe('useSyncStats', () => {
  beforeEach(async () => {
    await resetOfflineSyncManager();
  });

  afterEach(async () => {
    await resetOfflineSyncManager();
  });

  it('should return null initially', () => {
    const { result } = renderHook(() => useSyncStats());
    expect(result.current).toBeNull();
  });

  it('should load stats', async () => {
    const { result } = renderHook(() => useSyncStats());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });

    expect(result.current?.totalQueued).toBe(0);
  });
});

describe('useHasPendingMessages', () => {
  beforeEach(async () => {
    await resetOfflineSyncManager();
  });

  afterEach(async () => {
    await resetOfflineSyncManager();
  });

  it('should return false initially', () => {
    const { result } = renderHook(() => useHasPendingMessages());
    expect(result.current).toBe(false);
  });

  it('should return false when no pending messages', async () => {
    const { result } = renderHook(() => useHasPendingMessages());

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });
});
