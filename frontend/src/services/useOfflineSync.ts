/**
 * React Hook for Offline Sync Manager
 * 
 * Provides easy integration with React components
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getOfflineSyncManager,
  OfflineSyncManager,
  QueuedMessage,
  SyncStats,
  SyncResult,
  SyncCallbacks,
} from './OfflineSyncManager';

export interface UseOfflineSyncState {
  isInitialized: boolean;
  isSyncing: boolean;
  stats: SyncStats | null;
  error: Error | null;
}

export interface UseOfflineSyncActions {
  queueMessage: (message: Omit<QueuedMessage, 'id' | 'timestamp' | 'retryCount' | 'status'>) => Promise<string>;
  syncAll: () => Promise<SyncResult[]>;
  retryFailed: () => Promise<SyncResult[]>;
  getAllMessages: () => Promise<QueuedMessage[]>;
  getMessagesByStatus: (status: QueuedMessage['status']) => Promise<QueuedMessage[]>;
  deleteMessage: (messageId: string) => Promise<void>;
  clearAll: () => Promise<void>;
  refreshStats: () => Promise<void>;
  setAutoSync: (enabled: boolean) => void;
}

/**
 * Hook for using the OfflineSyncManager in React components
 */
export function useOfflineSync(callbacks?: SyncCallbacks): [UseOfflineSyncState, UseOfflineSyncActions] {
  const [manager, setManager] = useState<OfflineSyncManager | null>(null);
  const [state, setState] = useState<UseOfflineSyncState>({
    isInitialized: false,
    isSyncing: false,
    stats: null,
    error: null,
  });

  // Initialize the manager
  useEffect(() => {
    let mounted = true;

    const initManager = async () => {
      try {
        const syncCallbacks: SyncCallbacks = {
          onSyncStart: () => {
            if (mounted) {
              setState(prev => ({ ...prev, isSyncing: true }));
              callbacks?.onSyncStart?.();
            }
          },
          onSyncComplete: (results) => {
            if (mounted) {
              setState(prev => ({ ...prev, isSyncing: false }));
              refreshStats();
              callbacks?.onSyncComplete?.(results);
            }
          },
          onSyncError: (error) => {
            if (mounted) {
              setState(prev => ({ ...prev, isSyncing: false, error }));
              callbacks?.onSyncError?.(error);
            }
          },
          onMessageQueued: (message) => {
            if (mounted) {
              refreshStats();
              callbacks?.onMessageQueued?.(message);
            }
          },
        };

        const mgr = await getOfflineSyncManager(syncCallbacks);
        
        if (mounted) {
          setManager(mgr);
          setState(prev => ({ ...prev, isInitialized: true }));
          
          // Load initial stats
          const stats = await mgr.getSyncStats();
          setState(prev => ({ ...prev, stats }));
        }
      } catch (error) {
        if (mounted) {
          setState(prev => ({ ...prev, error: error as Error }));
        }
      }
    };

    initManager();

    return () => {
      mounted = false;
    };
  }, []);

  // Refresh stats helper
  const refreshStats = useCallback(async () => {
    if (manager) {
      try {
        const stats = await manager.getSyncStats();
        setState(prev => ({ ...prev, stats }));
      } catch (error) {
        console.error('Failed to refresh stats:', error);
      }
    }
  }, [manager]);

  // Actions
  const actions: UseOfflineSyncActions = {
    queueMessage: useCallback(async (message) => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      const messageId = await manager.queueMessage(message);
      await refreshStats();
      return messageId;
    }, [manager, refreshStats]),

    syncAll: useCallback(async () => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      return manager.syncAll();
    }, [manager]),

    retryFailed: useCallback(async () => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      return manager.retryFailedMessages();
    }, [manager]),

    getAllMessages: useCallback(async () => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      return manager.getAllMessages();
    }, [manager]),

    getMessagesByStatus: useCallback(async (status) => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      return manager.getMessagesByStatus(status);
    }, [manager]),

    deleteMessage: useCallback(async (messageId) => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      await manager.deleteMessage(messageId);
      await refreshStats();
    }, [manager, refreshStats]),

    clearAll: useCallback(async () => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      await manager.clearAll();
      await refreshStats();
    }, [manager, refreshStats]),

    refreshStats: useCallback(async () => {
      await refreshStats();
    }, [refreshStats]),

    setAutoSync: useCallback((enabled) => {
      if (!manager) {
        throw new Error('OfflineSyncManager not initialized');
      }
      manager.setAutoSync(enabled);
    }, [manager]),
  };

  return [state, actions];
}

/**
 * Simple hook to get sync statistics
 */
export function useSyncStats(): SyncStats | null {
  const [stats, setStats] = useState<SyncStats | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadStats = async () => {
      try {
        const manager = await getOfflineSyncManager();
        if (mounted) {
          const syncStats = await manager.getSyncStats();
          setStats(syncStats);
        }
      } catch (error) {
        console.error('Failed to load sync stats:', error);
      }
    };

    loadStats();

    // Refresh stats every 10 seconds
    const interval = setInterval(loadStats, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return stats;
}

/**
 * Hook to check if there are pending messages
 */
export function useHasPendingMessages(): boolean {
  const stats = useSyncStats();
  return stats ? stats.pendingCount > 0 : false;
}
