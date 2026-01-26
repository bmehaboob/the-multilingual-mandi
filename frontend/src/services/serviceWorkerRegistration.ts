/**
 * Service Worker Registration and Management
 * 
 * Handles PWA service worker registration, updates, and offline detection
 * Requirements: 12.7, 19.1
 */

import { Workbox } from 'workbox-window';

export interface ServiceWorkerCallbacks {
  onSuccess?: () => void;
  onUpdate?: () => void;
  onOffline?: () => void;
  onOnline?: () => void;
}

let workbox: Workbox | null = null;

/**
 * Register the service worker with Workbox
 * Requirement 19.1: Implement service workers for offline functionality
 */
export function registerServiceWorker(callbacks?: ServiceWorkerCallbacks): void {
  // Only register in production or when explicitly enabled
  if (import.meta.env.DEV && !import.meta.env.VITE_SW_DEV) {
    console.log('Service Worker registration skipped in development mode');
    return;
  }

  if ('serviceWorker' in navigator) {
    workbox = new Workbox('/sw.js');

    // Handle service worker installation
    workbox.addEventListener('installed', (event) => {
      if (event.isUpdate) {
        console.log('Service Worker updated');
        callbacks?.onUpdate?.();
      } else {
        console.log('Service Worker installed for the first time');
        callbacks?.onSuccess?.();
      }
    });

    // Handle service worker activation
    workbox.addEventListener('activated', (event) => {
      if (!event.isUpdate) {
        console.log('Service Worker activated');
      }
    });

    // Handle service worker waiting
    workbox.addEventListener('waiting', () => {
      console.log('New Service Worker waiting to activate');
      callbacks?.onUpdate?.();
    });

    // Handle service worker controlling
    workbox.addEventListener('controlling', () => {
      console.log('Service Worker is now controlling the page');
      // Reload the page to ensure all assets are from the new service worker
      window.location.reload();
    });

    // Register the service worker
    workbox.register().catch((error) => {
      console.error('Service Worker registration failed:', error);
    });

    // Monitor online/offline status
    // Requirement 12.4: Notify users when operating in offline mode
    window.addEventListener('online', () => {
      console.log('Network connection restored');
      callbacks?.onOnline?.();
    });

    window.addEventListener('offline', () => {
      console.log('Network connection lost');
      callbacks?.onOffline?.();
    });
  } else {
    console.warn('Service Workers are not supported in this browser');
  }
}

/**
 * Unregister the service worker
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready;
    return registration.unregister();
  }
  return false;
}

/**
 * Check if the app is currently online
 * Requirement 12.4: Detect offline mode
 */
export function isOnline(): boolean {
  return navigator.onLine;
}

/**
 * Skip waiting and activate the new service worker immediately
 * Used when user confirms they want to update the app
 */
export function skipWaiting(): void {
  if (workbox) {
    workbox.messageSkipWaiting();
  }
}

/**
 * Get the current service worker registration
 */
export async function getServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | undefined> {
  if ('serviceWorker' in navigator) {
    return navigator.serviceWorker.ready;
  }
  return undefined;
}

/**
 * Check if service worker is supported
 */
export function isServiceWorkerSupported(): boolean {
  return 'serviceWorker' in navigator;
}

/**
 * Clear all caches (useful for debugging or user-initiated cache clear)
 */
export async function clearAllCaches(): Promise<void> {
  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('All caches cleared');
  }
}

/**
 * Get cache statistics
 */
export async function getCacheStats(): Promise<{
  cacheNames: string[];
  totalSize: number;
}> {
  if (!('caches' in window)) {
    return { cacheNames: [], totalSize: 0 };
  }

  const cacheNames = await caches.keys();
  let totalSize = 0;

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        totalSize += blob.size;
      }
    }
  }

  return { cacheNames, totalSize };
}
