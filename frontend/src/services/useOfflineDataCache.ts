/**
 * React Hook for Offline Data Cache
 * 
 * Provides easy access to offline data caching functionality
 * Requirements: 12.2, 12.5, 12.6, 12.8
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getOfflineDataCache,
  type OfflineDataCache,
  type CachedPriceData,
  type NegotiationTemplate,
  type TransactionRecord,
  type UserPreferences,
} from './OfflineDataCache';

/**
 * Hook return type
 */
export interface UseOfflineDataCacheReturn {
  // Price data methods
  cachePriceData: (priceData: Omit<CachedPriceData, 'expiresAt'>) => Promise<void>;
  getCachedPriceData: (commodity: string) => Promise<CachedPriceData | null>;
  getAllCachedPriceData: () => Promise<CachedPriceData[]>;

  // Negotiation template methods
  cacheNegotiationTemplate: (template: NegotiationTemplate) => Promise<void>;
  cacheNegotiationTemplates: (templates: NegotiationTemplate[]) => Promise<void>;
  getNegotiationTemplate: (id: string) => Promise<NegotiationTemplate | null>;
  getNegotiationTemplatesByLanguage: (language: string) => Promise<NegotiationTemplate[]>;
  getNegotiationTemplatesByCategory: (
    category: NegotiationTemplate['category']
  ) => Promise<NegotiationTemplate[]>;

  // Transaction methods
  cacheTransaction: (transaction: TransactionRecord) => Promise<void>;
  getTransaction: (id: string) => Promise<TransactionRecord | null>;
  getRecentTransactions: (userId: string, limit?: number) => Promise<TransactionRecord[]>;

  // User preferences methods
  cacheUserPreferences: (preferences: UserPreferences) => Promise<void>;
  getUserPreferences: (userId: string) => Promise<UserPreferences | null>;
  updateUserPreferences: (
    userId: string,
    updates: Partial<Omit<UserPreferences, 'userId' | 'updatedAt'>>
  ) => Promise<void>;

  // Utility methods
  getCacheStats: () => Promise<{
    priceDataCount: number;
    negotiationTemplatesCount: number;
    transactionsCount: number;
    userPreferencesCount: number;
  }>;
  clearAll: () => Promise<void>;

  // State
  isInitialized: boolean;
  error: Error | null;
}

/**
 * React hook for offline data caching
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const cache = useOfflineDataCache();
 * 
 *   useEffect(() => {
 *     if (cache.isInitialized) {
 *       cache.cachePriceData({
 *         commodity: 'tomato',
 *         location: 'Maharashtra',
 *         minPrice: 15,
 *         maxPrice: 25,
 *         averagePrice: 20,
 *         medianPrice: 20,
 *         timestamp: Date.now(),
 *         source: 'demo',
 *       });
 *     }
 *   }, [cache.isInitialized]);
 * 
 *   return <div>Cache ready: {cache.isInitialized}</div>;
 * }
 * ```
 */
export function useOfflineDataCache(): UseOfflineDataCacheReturn {
  const [cache, setCache] = useState<OfflineDataCache | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Initialize cache on mount
  useEffect(() => {
    let mounted = true;

    const initCache = async () => {
      try {
        const cacheInstance = await getOfflineDataCache();
        if (mounted) {
          setCache(cacheInstance);
          setIsInitialized(true);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
          console.error('Failed to initialize offline data cache:', err);
        }
      }
    };

    initCache();

    return () => {
      mounted = false;
    };
  }, []);

  // Price data methods
  const cachePriceData = useCallback(
    async (priceData: Omit<CachedPriceData, 'expiresAt'>) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.cachePriceData(priceData);
    },
    [cache]
  );

  const getCachedPriceData = useCallback(
    async (commodity: string) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getCachedPriceData(commodity);
    },
    [cache]
  );

  const getAllCachedPriceData = useCallback(async () => {
    if (!cache) throw new Error('Cache not initialized');
    return cache.getAllCachedPriceData();
  }, [cache]);

  // Negotiation template methods
  const cacheNegotiationTemplate = useCallback(
    async (template: NegotiationTemplate) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.cacheNegotiationTemplate(template);
    },
    [cache]
  );

  const cacheNegotiationTemplates = useCallback(
    async (templates: NegotiationTemplate[]) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.cacheNegotiationTemplates(templates);
    },
    [cache]
  );

  const getNegotiationTemplate = useCallback(
    async (id: string) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getNegotiationTemplate(id);
    },
    [cache]
  );

  const getNegotiationTemplatesByLanguage = useCallback(
    async (language: string) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getNegotiationTemplatesByLanguage(language);
    },
    [cache]
  );

  const getNegotiationTemplatesByCategory = useCallback(
    async (category: NegotiationTemplate['category']) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getNegotiationTemplatesByCategory(category);
    },
    [cache]
  );

  // Transaction methods
  const cacheTransaction = useCallback(
    async (transaction: TransactionRecord) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.cacheTransaction(transaction);
    },
    [cache]
  );

  const getTransaction = useCallback(
    async (id: string) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getTransaction(id);
    },
    [cache]
  );

  const getRecentTransactions = useCallback(
    async (userId: string, limit: number = 5) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getRecentTransactions(userId, limit);
    },
    [cache]
  );

  // User preferences methods
  const cacheUserPreferences = useCallback(
    async (preferences: UserPreferences) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.cacheUserPreferences(preferences);
    },
    [cache]
  );

  const getUserPreferences = useCallback(
    async (userId: string) => {
      if (!cache) throw new Error('Cache not initialized');
      return cache.getUserPreferences(userId);
    },
    [cache]
  );

  const updateUserPreferences = useCallback(
    async (
      userId: string,
      updates: Partial<Omit<UserPreferences, 'userId' | 'updatedAt'>>
    ) => {
      if (!cache) throw new Error('Cache not initialized');
      await cache.updateUserPreferences(userId, updates);
    },
    [cache]
  );

  // Utility methods
  const getCacheStats = useCallback(async () => {
    if (!cache) throw new Error('Cache not initialized');
    return cache.getCacheStats();
  }, [cache]);

  const clearAll = useCallback(async () => {
    if (!cache) throw new Error('Cache not initialized');
    await cache.clearAll();
  }, [cache]);

  return {
    // Price data methods
    cachePriceData,
    getCachedPriceData,
    getAllCachedPriceData,

    // Negotiation template methods
    cacheNegotiationTemplate,
    cacheNegotiationTemplates,
    getNegotiationTemplate,
    getNegotiationTemplatesByLanguage,
    getNegotiationTemplatesByCategory,

    // Transaction methods
    cacheTransaction,
    getTransaction,
    getRecentTransactions,

    // User preferences methods
    cacheUserPreferences,
    getUserPreferences,
    updateUserPreferences,

    // Utility methods
    getCacheStats,
    clearAll,

    // State
    isInitialized,
    error,
  };
}
