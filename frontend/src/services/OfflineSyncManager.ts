/**
 * Offline Sync Manager
 * 
 * Manages offline message queueing and synchronization using IndexedDB
 * Requirements: 12.1, 12.3
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';

/**
 * Message to be queued for offline transmission
 */
export interface QueuedMessage {
  id: string;
  conversationId: string;
  senderId: string;
  recipientId: string;
  originalText: string;
  originalLanguage: string;
  audioBlob?: Blob;
  timestamp: number;
  retryCount: number;
  status: 'pending' | 'syncing' | 'failed';
}

/**
 * Sync statistics
 */
export interface SyncStats {
  totalQueued: number;
  pendingCount: number;
  syncingCount: number;
  failedCount: number;
  lastSyncTime?: number;
}

/**
 * Sync result for a single message
 */
export interface SyncResult {
  messageId: string;
  success: boolean;
  error?: string;
}

/**
 * Callback for sync events
 */
export interface SyncCallbacks {
  onSyncStart?: () => void;
  onSyncComplete?: (results: SyncResult[]) => void;
  onSyncError?: (error: Error) => void;
  onMessageQueued?: (message: QueuedMessage) => void;
}

/**
 * IndexedDB Schema
 */
interface OfflineSyncDB extends DBSchema {
  messages: {
    key: string;
    value: QueuedMessage;
    indexes: {
      'by-status': string;
      'by-timestamp': number;
      'by-conversation': string;
    };
  };
}

const DB_NAME = 'multilingual-mandi-offline';
const DB_VERSION = 1;
const STORE_NAME = 'messages';
const MAX_RETRY_COUNT = 3;

/**
 * OfflineSyncManager
 * 
 * Handles offline message queueing and automatic synchronization
 * Requirement 12.1: Allow users to record voice messages for later transmission
 * Requirement 12.3: Automatically sync queued messages when connectivity restored
 */
export class OfflineSyncManager {
  private db: IDBPDatabase<OfflineSyncDB> | null = null;
  private callbacks: SyncCallbacks = {};
  private syncInProgress = false;
  private autoSyncEnabled = true;
  private onlineListener: (() => void) | null = null;

  /**
   * Initialize the offline sync manager
   */
  async initialize(callbacks?: SyncCallbacks): Promise<void> {
    this.callbacks = callbacks || {};
    
    // Open IndexedDB
    this.db = await openDB<OfflineSyncDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Create messages store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          
          // Create indexes for efficient querying
          store.createIndex('by-status', 'status');
          store.createIndex('by-timestamp', 'timestamp');
          store.createIndex('by-conversation', 'conversationId');
        }
      },
    });

    // Set up auto-sync when connectivity is restored
    this.setupAutoSync();

    console.log('OfflineSyncManager initialized');
  }

  /**
   * Set up automatic synchronization when online
   * Requirement 12.3: Auto-sync when connectivity restored
   */
  private setupAutoSync(): void {
    this.onlineListener = () => {
      if (this.autoSyncEnabled && navigator.onLine) {
        console.log('Network connection restored, starting auto-sync');
        this.syncAll().catch((error) => {
          console.error('Auto-sync failed:', error);
        });
      }
    };

    window.addEventListener('online', this.onlineListener);
  }

  /**
   * Queue a message for offline transmission
   * Requirement 12.1: Record voice messages for later transmission
   */
  async queueMessage(message: Omit<QueuedMessage, 'id' | 'timestamp' | 'retryCount' | 'status'>): Promise<string> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    const queuedMessage: QueuedMessage = {
      ...message,
      id: this.generateMessageId(),
      timestamp: Date.now(),
      retryCount: 0,
      status: 'pending',
    };

    await this.db.add(STORE_NAME, queuedMessage);
    
    console.log(`Message queued: ${queuedMessage.id}`);
    this.callbacks.onMessageQueued?.(queuedMessage);

    return queuedMessage.id;
  }

  /**
   * Get all queued messages
   */
  async getAllMessages(): Promise<QueuedMessage[]> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    return this.db.getAll(STORE_NAME);
  }

  /**
   * Get messages by status
   */
  async getMessagesByStatus(status: QueuedMessage['status']): Promise<QueuedMessage[]> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    return this.db.getAllFromIndex(STORE_NAME, 'by-status', status);
  }

  /**
   * Get messages by conversation
   */
  async getMessagesByConversation(conversationId: string): Promise<QueuedMessage[]> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    return this.db.getAllFromIndex(STORE_NAME, 'by-conversation', conversationId);
  }

  /**
   * Get sync statistics
   */
  async getSyncStats(): Promise<SyncStats> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    const allMessages = await this.getAllMessages();
    const pendingMessages = allMessages.filter(m => m.status === 'pending');
    const syncingMessages = allMessages.filter(m => m.status === 'syncing');
    const failedMessages = allMessages.filter(m => m.status === 'failed');

    // Get last sync time from most recent successfully synced message
    const syncedMessages = allMessages.filter(m => m.status === 'pending' && m.retryCount > 0);
    const lastSyncTime = syncedMessages.length > 0
      ? Math.max(...syncedMessages.map(m => m.timestamp))
      : undefined;

    return {
      totalQueued: allMessages.length,
      pendingCount: pendingMessages.length,
      syncingCount: syncingMessages.length,
      failedCount: failedMessages.length,
      lastSyncTime,
    };
  }

  /**
   * Synchronize all pending messages
   * Requirement 12.3: Auto-sync when connectivity restored
   */
  async syncAll(): Promise<SyncResult[]> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    if (this.syncInProgress) {
      console.log('Sync already in progress, skipping');
      return [];
    }

    if (!navigator.onLine) {
      console.log('Cannot sync: offline');
      return [];
    }

    this.syncInProgress = true;
    this.callbacks.onSyncStart?.();

    const results: SyncResult[] = [];

    try {
      // Get all pending messages, ordered by timestamp (FIFO)
      const pendingMessages = await this.getMessagesByStatus('pending');
      const sortedMessages = pendingMessages.sort((a, b) => a.timestamp - b.timestamp);

      console.log(`Starting sync of ${sortedMessages.length} messages`);

      // Sync messages one by one
      for (const message of sortedMessages) {
        const result = await this.syncMessage(message);
        results.push(result);
      }

      console.log(`Sync complete: ${results.filter(r => r.success).length}/${results.length} successful`);
      this.callbacks.onSyncComplete?.(results);

      return results;
    } catch (error) {
      console.error('Sync failed:', error);
      this.callbacks.onSyncError?.(error as Error);
      throw error;
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * Synchronize a single message
   */
  private async syncMessage(message: QueuedMessage): Promise<SyncResult> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    try {
      // Update status to syncing
      await this.updateMessageStatus(message.id, 'syncing');

      // Send message to backend
      const success = await this.sendMessageToBackend(message);

      if (success) {
        // Remove from queue on success
        await this.db.delete(STORE_NAME, message.id);
        console.log(`Message ${message.id} synced successfully`);
        
        return {
          messageId: message.id,
          success: true,
        };
      } else {
        // Increment retry count and update status
        const updatedMessage = {
          ...message,
          retryCount: message.retryCount + 1,
          status: message.retryCount + 1 >= MAX_RETRY_COUNT ? 'failed' : 'pending',
        } as QueuedMessage;

        await this.db.put(STORE_NAME, updatedMessage);
        
        console.log(`Message ${message.id} sync failed (retry ${updatedMessage.retryCount}/${MAX_RETRY_COUNT})`);
        
        return {
          messageId: message.id,
          success: false,
          error: 'Sync failed',
        };
      }
    } catch (error) {
      console.error(`Error syncing message ${message.id}:`, error);
      
      // Update status back to pending for retry
      await this.updateMessageStatus(message.id, 'pending');
      
      return {
        messageId: message.id,
        success: false,
        error: (error as Error).message,
      };
    }
  }

  /**
   * Send message to backend API
   * This is a placeholder that should be replaced with actual API call
   */
  private async sendMessageToBackend(message: QueuedMessage): Promise<boolean> {
    // TODO: Replace with actual API endpoint
    // For now, this is a mock implementation
    
    try {
      const formData = new FormData();
      formData.append('conversationId', message.conversationId);
      formData.append('senderId', message.senderId);
      formData.append('recipientId', message.recipientId);
      formData.append('originalText', message.originalText);
      formData.append('originalLanguage', message.originalLanguage);
      
      if (message.audioBlob) {
        formData.append('audio', message.audioBlob, 'audio.webm');
      }

      const response = await fetch('/api/messages', {
        method: 'POST',
        body: formData,
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to send message to backend:', error);
      return false;
    }
  }

  /**
   * Update message status
   */
  private async updateMessageStatus(messageId: string, status: QueuedMessage['status']): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    const message = await this.db.get(STORE_NAME, messageId);
    if (message) {
      message.status = status;
      await this.db.put(STORE_NAME, message);
    }
  }

  /**
   * Retry failed messages
   */
  async retryFailedMessages(): Promise<SyncResult[]> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    const failedMessages = await this.getMessagesByStatus('failed');
    
    // Reset failed messages to pending
    for (const message of failedMessages) {
      message.status = 'pending';
      message.retryCount = 0;
      await this.db.put(STORE_NAME, message);
    }

    // Trigger sync
    return this.syncAll();
  }

  /**
   * Delete a specific message from the queue
   */
  async deleteMessage(messageId: string): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    await this.db.delete(STORE_NAME, messageId);
    console.log(`Message ${messageId} deleted from queue`);
  }

  /**
   * Clear all messages from the queue
   */
  async clearAll(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineSyncManager not initialized');
    }

    await this.db.clear(STORE_NAME);
    console.log('All queued messages cleared');
  }

  /**
   * Enable or disable auto-sync
   */
  setAutoSync(enabled: boolean): void {
    this.autoSyncEnabled = enabled;
    console.log(`Auto-sync ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Check if sync is currently in progress
   */
  isSyncing(): boolean {
    return this.syncInProgress;
  }

  /**
   * Clean up resources
   */
  async destroy(): Promise<void> {
    if (this.onlineListener) {
      window.removeEventListener('online', this.onlineListener);
      this.onlineListener = null;
    }

    if (this.db) {
      this.db.close();
      this.db = null;
    }

    console.log('OfflineSyncManager destroyed');
  }

  /**
   * Generate a unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Singleton instance
let offlineSyncManagerInstance: OfflineSyncManager | null = null;

/**
 * Get the singleton instance of OfflineSyncManager
 */
export async function getOfflineSyncManager(callbacks?: SyncCallbacks): Promise<OfflineSyncManager> {
  if (!offlineSyncManagerInstance) {
    offlineSyncManagerInstance = new OfflineSyncManager();
    await offlineSyncManagerInstance.initialize(callbacks);
  }
  return offlineSyncManagerInstance;
}

/**
 * Reset the singleton instance (useful for testing)
 */
export async function resetOfflineSyncManager(): Promise<void> {
  if (offlineSyncManagerInstance) {
    await offlineSyncManagerInstance.destroy();
    offlineSyncManagerInstance = null;
  }
}
