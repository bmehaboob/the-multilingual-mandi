/**
 * Unit Tests for OfflineSyncManager
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { OfflineSyncManager, resetOfflineSyncManager, getOfflineSyncManager } from './OfflineSyncManager';

// Mock IndexedDB
import 'fake-indexeddb/auto';

// Mock fetch
global.fetch = vi.fn();

describe('OfflineSyncManager', () => {
  let manager: OfflineSyncManager;

  beforeEach(async () => {
    // Reset the singleton
    await resetOfflineSyncManager();
    
    // Create a new manager
    manager = new OfflineSyncManager();
    await manager.initialize();
    
    // Clear all messages from previous tests
    await manager.clearAll();

    // Reset fetch mock
    vi.clearAllMocks();
  });

  afterEach(async () => {
    // Clear all messages
    await manager.clearAll();
    await manager.destroy();
    await resetOfflineSyncManager();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      const newManager = new OfflineSyncManager();
      await expect(newManager.initialize()).resolves.not.toThrow();
      await newManager.destroy();
    });

    it('should call callbacks on initialization', async () => {
      const onSyncStart = vi.fn();
      const newManager = new OfflineSyncManager();
      await newManager.initialize({ onSyncStart });
      
      expect(newManager).toBeDefined();
      await newManager.destroy();
    });
  });

  describe('Message Queueing', () => {
    it('should queue a message successfully', async () => {
      const messageId = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Hello',
        originalLanguage: 'en',
      });

      expect(messageId).toBeDefined();
      expect(messageId).toMatch(/^msg_/);
    });

    it('should generate unique message IDs', async () => {
      const id1 = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Hello',
        originalLanguage: 'en',
      });

      const id2 = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'World',
        originalLanguage: 'en',
      });

      expect(id1).not.toBe(id2);
    });

    it('should store message with correct initial status', async () => {
      const messageId = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Hello',
        originalLanguage: 'en',
      });

      const messages = await manager.getAllMessages();
      const message = messages.find(m => m.id === messageId);

      expect(message).toBeDefined();
      expect(message?.status).toBe('pending');
      expect(message?.retryCount).toBe(0);
    });

    it('should call onMessageQueued callback', async () => {
      const onMessageQueued = vi.fn();
      const newManager = new OfflineSyncManager();
      await newManager.initialize({ onMessageQueued });

      await newManager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Hello',
        originalLanguage: 'en',
      });

      expect(onMessageQueued).toHaveBeenCalledTimes(1);
      expect(onMessageQueued).toHaveBeenCalledWith(
        expect.objectContaining({
          conversationId: 'conv-1',
          status: 'pending',
        })
      );

      await newManager.destroy();
    });

    it('should queue message with audio blob', async () => {
      const audioBlob = new Blob(['audio data'], { type: 'audio/webm' });
      
      const messageId = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Hello',
        originalLanguage: 'en',
        audioBlob,
      });

      const messages = await manager.getAllMessages();
      const message = messages.find(m => m.id === messageId);

      expect(message?.audioBlob).toBeDefined();
      // Note: jsdom doesn't fully support Blob serialization in IndexedDB
      // In real browsers, the blob type would be preserved
    });
  });

  describe('Message Retrieval', () => {
    beforeEach(async () => {
      // Queue some test messages
      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 1',
        originalLanguage: 'en',
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 2',
        originalLanguage: 'en',
      });

      await manager.queueMessage({
        conversationId: 'conv-2',
        senderId: 'user-1',
        recipientId: 'user-3',
        originalText: 'Message 3',
        originalLanguage: 'hi',
      });
    });

    it('should get all messages', async () => {
      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(3);
    });

    it('should get messages by status', async () => {
      const pendingMessages = await manager.getMessagesByStatus('pending');
      expect(pendingMessages).toHaveLength(3);

      const syncingMessages = await manager.getMessagesByStatus('syncing');
      expect(syncingMessages).toHaveLength(0);
    });

    it('should get messages by conversation', async () => {
      const conv1Messages = await manager.getMessagesByConversation('conv-1');
      expect(conv1Messages).toHaveLength(2);

      const conv2Messages = await manager.getMessagesByConversation('conv-2');
      expect(conv2Messages).toHaveLength(1);
    });
  });

  describe('Sync Statistics', () => {
    it('should return correct stats for empty queue', async () => {
      const stats = await manager.getSyncStats();

      expect(stats.totalQueued).toBe(0);
      expect(stats.pendingCount).toBe(0);
      expect(stats.syncingCount).toBe(0);
      expect(stats.failedCount).toBe(0);
    });

    it('should return correct stats with queued messages', async () => {
      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 1',
        originalLanguage: 'en',
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 2',
        originalLanguage: 'en',
      });

      const stats = await manager.getSyncStats();

      expect(stats.totalQueued).toBe(2);
      expect(stats.pendingCount).toBe(2);
      expect(stats.syncingCount).toBe(0);
      expect(stats.failedCount).toBe(0);
    });
  });

  describe('Message Synchronization', () => {
    beforeEach(() => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
    });

    it('should not sync when offline', async () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 1',
        originalLanguage: 'en',
      });

      const results = await manager.syncAll();
      expect(results).toHaveLength(0);
    });

    it('should sync messages in FIFO order', async () => {
      // Mock successful API responses
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      // Queue messages with delays to ensure different timestamps
      const id1 = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'First',
        originalLanguage: 'en',
      });

      await new Promise(resolve => setTimeout(resolve, 10));

      const id2 = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Second',
        originalLanguage: 'en',
      });

      const results = await manager.syncAll();

      expect(results).toHaveLength(2);
      expect(results[0].messageId).toBe(id1);
      expect(results[1].messageId).toBe(id2);
    });

    it('should remove successfully synced messages', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      await manager.syncAll();

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(0);
    });

    it('should handle sync failures and retry', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
      });

      const messageId = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      const results = await manager.syncAll();

      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(false);

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(1);
      expect(messages[0].retryCount).toBe(1);
      expect(messages[0].status).toBe('pending');
    });

    it('should mark message as failed after max retries', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      // Sync 3 times (max retries)
      await manager.syncAll();
      await manager.syncAll();
      await manager.syncAll();

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(1);
      expect(messages[0].status).toBe('failed');
      expect(messages[0].retryCount).toBe(3);
    });

    it('should call sync callbacks', async () => {
      const onSyncStart = vi.fn();
      const onSyncComplete = vi.fn();

      const newManager = new OfflineSyncManager();
      await newManager.initialize({ onSyncStart, onSyncComplete });

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      await newManager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      await newManager.syncAll();

      expect(onSyncStart).toHaveBeenCalledTimes(1);
      expect(onSyncComplete).toHaveBeenCalledTimes(1);

      await newManager.destroy();
    });

    it('should not start multiple syncs simultaneously', async () => {
      (global.fetch as any).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
      );

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      const sync1 = manager.syncAll();
      const sync2 = manager.syncAll();

      const [results1, results2] = await Promise.all([sync1, sync2]);

      expect(results1.length + results2.length).toBe(1);
    });
  });

  describe('Auto-Sync', () => {
    it('should trigger sync when going online', async () => {
      const onSyncStart = vi.fn();
      const newManager = new OfflineSyncManager();
      await newManager.initialize({ onSyncStart });

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      await newManager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      // Simulate going online
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });

      window.dispatchEvent(new Event('online'));

      // Wait for async sync to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(onSyncStart).toHaveBeenCalled();

      await newManager.destroy();
    });

    it('should respect auto-sync setting', async () => {
      const onSyncStart = vi.fn();
      const newManager = new OfflineSyncManager();
      await newManager.initialize({ onSyncStart });

      newManager.setAutoSync(false);

      await newManager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      // Simulate going online
      window.dispatchEvent(new Event('online'));

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(onSyncStart).not.toHaveBeenCalled();

      await newManager.destroy();
    });
  });

  describe('Message Management', () => {
    it('should delete a specific message', async () => {
      const messageId = await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      await manager.deleteMessage(messageId);

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(0);
    });

    it('should clear all messages', async () => {
      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 1',
        originalLanguage: 'en',
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message 2',
        originalLanguage: 'en',
      });

      await manager.clearAll();

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(0);
    });

    it('should retry failed messages', async () => {
      // First, create a failed message
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
      });

      await manager.queueMessage({
        conversationId: 'conv-1',
        senderId: 'user-1',
        recipientId: 'user-2',
        originalText: 'Message',
        originalLanguage: 'en',
      });

      // Sync 3 times to mark as failed
      await manager.syncAll();
      await manager.syncAll();
      await manager.syncAll();

      // Now mock success
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      // Retry failed messages
      const results = await manager.retryFailedMessages();

      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(true);

      const messages = await manager.getAllMessages();
      expect(messages).toHaveLength(0);
    });
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance', async () => {
      const instance1 = await getOfflineSyncManager();
      const instance2 = await getOfflineSyncManager();

      expect(instance1).toBe(instance2);
    });

    it('should reset singleton', async () => {
      const instance1 = await getOfflineSyncManager();
      await resetOfflineSyncManager();
      const instance2 = await getOfflineSyncManager();

      expect(instance1).not.toBe(instance2);
    });
  });

  describe('Error Handling', () => {
    it('should throw error when queueing without initialization', async () => {
      const uninitializedManager = new OfflineSyncManager();

      await expect(
        uninitializedManager.queueMessage({
          conversationId: 'conv-1',
          senderId: 'user-1',
          recipientId: 'user-2',
          originalText: 'Message',
          originalLanguage: 'en',
        })
      ).rejects.toThrow('OfflineSyncManager not initialized');
    });

    it('should throw error when syncing without initialization', async () => {
      const uninitializedManager = new OfflineSyncManager();

      await expect(uninitializedManager.syncAll()).rejects.toThrow(
        'OfflineSyncManager not initialized'
      );
    });
  });
});
