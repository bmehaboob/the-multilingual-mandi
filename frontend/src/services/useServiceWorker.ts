/**
 * React Hook for Service Worker Management
 * 
 * Provides offline detection, update notifications, and cache management
 * Requirements: 12.4, 12.7, 19.1
 */

import { useEffect, useState } from 'react';
import {
  registerServiceWorker,
  skipWaiting,
  isOnline as checkIsOnline,
  getCacheStats,
} from './serviceWorkerRegistration';

export interface ServiceWorkerState {
  isOnline: boolean;
  isUpdateAvailable: boolean;
  isInstalled: boolean;
  cacheStats: {
    cacheNames: string[];
    totalSize: number;
  } | null;
}

export interface ServiceWorkerActions {
  updateServiceWorker: () => void;
  refreshCacheStats: () => Promise<void>;
}

/**
 * Hook for managing service worker state and offline detection
 * Requirement 12.4: Notify users when operating in offline mode
 * Requirement 19.1: Service workers for offline functionality
 */
export function useServiceWorker(): [ServiceWorkerState, ServiceWorkerActions] {
  const [isOnline, setIsOnline] = useState<boolean>(checkIsOnline());
  const [isUpdateAvailable, setIsUpdateAvailable] = useState<boolean>(false);
  const [isInstalled, setIsInstalled] = useState<boolean>(false);
  const [cacheStats, setCacheStats] = useState<{
    cacheNames: string[];
    totalSize: number;
  } | null>(null);

  useEffect(() => {
    // Register service worker with callbacks
    registerServiceWorker({
      onSuccess: () => {
        setIsInstalled(true);
        console.log('Service Worker installed successfully');
      },
      onUpdate: () => {
        setIsUpdateAvailable(true);
        console.log('Service Worker update available');
      },
      onOffline: () => {
        setIsOnline(false);
        console.log('App is now offline');
      },
      onOnline: () => {
        setIsOnline(true);
        console.log('App is now online');
      },
    });

    // Initial cache stats
    refreshCacheStats();

    // Cleanup is not needed as service worker persists
  }, []);

  const updateServiceWorker = () => {
    skipWaiting();
    setIsUpdateAvailable(false);
  };

  const refreshCacheStats = async () => {
    try {
      const stats = await getCacheStats();
      setCacheStats(stats);
    } catch (error) {
      console.error('Failed to get cache stats:', error);
    }
  };

  return [
    {
      isOnline,
      isUpdateAvailable,
      isInstalled,
      cacheStats,
    },
    {
      updateServiceWorker,
      refreshCacheStats,
    },
  ];
}

/**
 * Simple hook for just offline detection
 * Requirement 12.4: Detect offline mode
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(checkIsOnline());

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
