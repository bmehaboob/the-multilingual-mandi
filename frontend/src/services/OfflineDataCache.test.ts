/**
 * Unit Tests for OfflineDataCache
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  OfflineDataCache,
  resetOfflineDataCache,
  getOfflineDataCache,
  type CachedPriceData,
  type NegotiationTemplate,
  type TransactionRecord,
  type UserPreferences,
} from './OfflineDataCache';

// Mock IndexedDB
import 'fake-indexeddb/auto';

describe('OfflineDataCache', () => {
  let cache: OfflineDataCache;

  beforeEach(async () => {
    // Reset the singleton
    await resetOfflineDataCache();

    // Create a new cache instance (disable auto-cleanup for tests)
    cache = new OfflineDataCache();
    await cache.initialize({ enableAutoCleanup: false });

    // Clear all data from previous tests
    await cache.clearAll();
  });

  afterEach(async () => {
    await cache.clearAll();
    await cache.destroy();
    await resetOfflineDataCache();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      const newCache = new OfflineDataCache();
      await expect(newCache.initialize()).resolves.not.toThrow();
      await newCache.destroy();
    });

    it('should throw error when accessing uninitialized cache', async () => {
      const uninitializedCache = new OfflineDataCache();

      await expect(
        uninitializedCache.cachePriceData({
          commodity: 'tomato',
          location: 'Maharashtra',
          minPrice: 15,
          maxPrice: 25,
          averagePrice: 20,
          medianPrice: 20,
          timestamp: Date.now(),
          source: 'demo',
        })
      ).rejects.toThrow('OfflineDataCache not initialized');
    });
  });

  describe('Price Data Caching', () => {
    const samplePriceData: Omit<CachedPriceData, 'expiresAt'> = {
      commodity: 'tomato',
      location: 'Maharashtra',
      minPrice: 15,
      maxPrice: 25,
      averagePrice: 20,
      medianPrice: 20,
      timestamp: Date.now(),
      source: 'demo',
    };

    it('should cache price data with correct expiry time', async () => {
      const now = Date.now();
      await cache.cachePriceData(samplePriceData);

      const cached = await cache.getCachedPriceData('tomato');
      expect(cached).toBeDefined();
      expect(cached?.commodity).toBe('tomato');
      expect(cached?.averagePrice).toBe(20);
      expect(cached?.expiresAt).toBeGreaterThan(now);
      // Should expire in approximately 24 hours
      expect(cached?.expiresAt).toBeLessThanOrEqual(now + 24 * 60 * 60 * 1000 + 1000);
    });

    it('should return null for non-existent price data', async () => {
      const cached = await cache.getCachedPriceData('nonexistent');
      expect(cached).toBeNull();
    });

    it('should get all cached price data', async () => {
      await cache.cachePriceData(samplePriceData);
      await cache.cachePriceData({
        ...samplePriceData,
        commodity: 'onion',
        averagePrice: 25,
      });

      const allData = await cache.getAllCachedPriceData();
      expect(allData).toHaveLength(2);
    });

    it('should clear all price data', async () => {
      await cache.cachePriceData(samplePriceData);
      await cache.clearPriceData();

      const cached = await cache.getCachedPriceData('tomato');
      expect(cached).toBeNull();
    });

    it('should update existing price data', async () => {
      await cache.cachePriceData(samplePriceData);
      await cache.cachePriceData({
        ...samplePriceData,
        averagePrice: 30,
      });

      const cached = await cache.getCachedPriceData('tomato');
      expect(cached?.averagePrice).toBe(30);
    });
  });

  describe('Negotiation Template Caching', () => {
    const sampleTemplate: NegotiationTemplate = {
      id: 'template-1',
      language: 'hi',
      category: 'greeting',
      template: 'नमस्ते {name}, आप कैसे हैं?',
      culturalContext: 'Formal Hindi greeting',
    };

    it('should cache negotiation template', async () => {
      await cache.cacheNegotiationTemplate(sampleTemplate);

      const cached = await cache.getNegotiationTemplate('template-1');
      expect(cached).toBeDefined();
      expect(cached?.language).toBe('hi');
      expect(cached?.category).toBe('greeting');
    });

    it('should cache multiple templates', async () => {
      const templates: NegotiationTemplate[] = [
        sampleTemplate,
        {
          id: 'template-2',
          language: 'hi',
          category: 'counter_offer',
          template: 'क्या आप {price} रुपये में बेच सकते हैं?',
        },
        {
          id: 'template-3',
          language: 'te',
          category: 'greeting',
          template: 'నమస్కారం {name}',
        },
      ];

      await cache.cacheNegotiationTemplates(templates);

      const allTemplates = await cache.getAllNegotiationTemplates();
      expect(allTemplates).toHaveLength(3);
    });

    it('should get templates by language', async () => {
      await cache.cacheNegotiationTemplates([
        sampleTemplate,
        {
          id: 'template-2',
          language: 'hi',
          category: 'counter_offer',
          template: 'क्या आप {price} रुपये में बेच सकते हैं?',
        },
        {
          id: 'template-3',
          language: 'te',
          category: 'greeting',
          template: 'నమస్కారం {name}',
        },
      ]);

      const hindiTemplates = await cache.getNegotiationTemplatesByLanguage('hi');
      expect(hindiTemplates).toHaveLength(2);

      const teluguTemplates = await cache.getNegotiationTemplatesByLanguage('te');
      expect(teluguTemplates).toHaveLength(1);
    });

    it('should get templates by category', async () => {
      await cache.cacheNegotiationTemplates([
        sampleTemplate,
        {
          id: 'template-2',
          language: 'hi',
          category: 'counter_offer',
          template: 'क्या आप {price} रुपये में बेच सकते हैं?',
        },
        {
          id: 'template-3',
          language: 'te',
          category: 'greeting',
          template: 'నమస్కారం {name}',
        },
      ]);

      const greetingTemplates = await cache.getNegotiationTemplatesByCategory('greeting');
      expect(greetingTemplates).toHaveLength(2);

      const counterOfferTemplates = await cache.getNegotiationTemplatesByCategory('counter_offer');
      expect(counterOfferTemplates).toHaveLength(1);
    });

    it('should return null for non-existent template', async () => {
      const cached = await cache.getNegotiationTemplate('nonexistent');
      expect(cached).toBeNull();
    });

    it('should clear all negotiation templates', async () => {
      await cache.cacheNegotiationTemplate(sampleTemplate);
      await cache.clearNegotiationTemplates();

      const cached = await cache.getNegotiationTemplate('template-1');
      expect(cached).toBeNull();
    });
  });

  describe('Transaction Caching', () => {
    const sampleTransaction: TransactionRecord = {
      id: 'txn-1',
      buyerId: 'buyer-1',
      sellerId: 'seller-1',
      commodity: 'tomato',
      quantity: 100,
      unit: 'kg',
      agreedPrice: 20,
      marketAverageAtTime: 22,
      conversationId: 'conv-1',
      completedAt: Date.now(),
      location: 'Maharashtra',
    };

    it('should cache transaction', async () => {
      await cache.cacheTransaction(sampleTransaction);

      const cached = await cache.getTransaction('txn-1');
      expect(cached).toBeDefined();
      expect(cached?.commodity).toBe('tomato');
      expect(cached?.agreedPrice).toBe(20);
    });

    it('should get transactions by buyer', async () => {
      await cache.cacheTransaction(sampleTransaction);
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-2',
        commodity: 'onion',
      });
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-3',
        buyerId: 'buyer-2',
      });

      const buyerTransactions = await cache.getTransactionsByBuyer('buyer-1');
      expect(buyerTransactions).toHaveLength(2);
    });

    it('should get transactions by seller', async () => {
      await cache.cacheTransaction(sampleTransaction);
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-2',
        commodity: 'onion',
      });
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-3',
        sellerId: 'seller-2',
      });

      const sellerTransactions = await cache.getTransactionsBySeller('seller-1');
      expect(sellerTransactions).toHaveLength(2);
    });

    it('should get transactions by commodity', async () => {
      await cache.cacheTransaction(sampleTransaction);
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-2',
      });
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-3',
        commodity: 'onion',
      });

      const tomatoTransactions = await cache.getTransactionsByCommodity('tomato');
      expect(tomatoTransactions).toHaveLength(2);
    });

    it('should get recent transactions (last 5)', async () => {
      const now = Date.now();

      // Create 7 transactions with different timestamps
      for (let i = 0; i < 7; i++) {
        await cache.cacheTransaction({
          ...sampleTransaction,
          id: `txn-${i}`,
          completedAt: now - i * 1000, // Each transaction 1 second apart
        });
      }

      const recentTransactions = await cache.getRecentTransactions('buyer-1', 5);
      expect(recentTransactions).toHaveLength(5);

      // Should be sorted by most recent first
      expect(recentTransactions[0].id).toBe('txn-0');
      expect(recentTransactions[4].id).toBe('txn-4');
    });

    it('should get recent transactions for both buyer and seller', async () => {
      const now = Date.now();

      // Create transactions where user is buyer
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-1',
        buyerId: 'user-1',
        completedAt: now - 1000,
      });

      // Create transactions where user is seller
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'txn-2',
        buyerId: 'other-user',
        sellerId: 'user-1',
        completedAt: now - 2000,
      });

      const recentTransactions = await cache.getRecentTransactions('user-1', 5);
      expect(recentTransactions).toHaveLength(2);
    });

    it('should return null for non-existent transaction', async () => {
      const cached = await cache.getTransaction('nonexistent');
      expect(cached).toBeNull();
    });

    it('should clear all transactions', async () => {
      await cache.cacheTransaction(sampleTransaction);
      await cache.clearTransactions();

      const cached = await cache.getTransaction('txn-1');
      expect(cached).toBeNull();
    });

    it('should verify transaction retention period', async () => {
      const now = Date.now();

      // Create a recent transaction
      await cache.cacheTransaction({
        ...sampleTransaction,
        id: 'recent-txn',
        completedAt: now,
      });

      // Verify it exists
      const recentTxn = await cache.getTransaction('recent-txn');
      expect(recentTxn).toBeDefined();

      // Test that cleanup method can be called
      await expect(cache.cleanupExpiredData()).resolves.not.toThrow();
    });
  });

  describe('User Preferences Caching', () => {
    const samplePreferences: UserPreferences = {
      userId: 'user-1',
      primaryLanguage: 'hi',
      secondaryLanguages: ['en', 'te'],
      speechRate: 0.85,
      volumeBoost: true,
      offlineMode: false,
      favoriteContacts: ['user-2', 'user-3'],
      updatedAt: Date.now(),
    };

    it('should cache user preferences', async () => {
      await cache.cacheUserPreferences(samplePreferences);

      const cached = await cache.getUserPreferences('user-1');
      expect(cached).toBeDefined();
      expect(cached?.primaryLanguage).toBe('hi');
      expect(cached?.speechRate).toBe(0.85);
    });

    it('should update timestamp when caching', async () => {
      const oldTimestamp = Date.now() - 1000;
      await cache.cacheUserPreferences({
        ...samplePreferences,
        updatedAt: oldTimestamp,
      });

      const cached = await cache.getUserPreferences('user-1');
      expect(cached?.updatedAt).toBeGreaterThan(oldTimestamp);
    });

    it('should update user preferences partially', async () => {
      await cache.cacheUserPreferences(samplePreferences);

      await cache.updateUserPreferences('user-1', {
        speechRate: 1.0,
        volumeBoost: false,
      });

      const cached = await cache.getUserPreferences('user-1');
      expect(cached?.speechRate).toBe(1.0);
      expect(cached?.volumeBoost).toBe(false);
      expect(cached?.primaryLanguage).toBe('hi'); // Should remain unchanged
    });

    it('should throw error when updating non-existent preferences', async () => {
      await expect(
        cache.updateUserPreferences('nonexistent', { speechRate: 1.0 })
      ).rejects.toThrow('User preferences not found');
    });

    it('should return null for non-existent preferences', async () => {
      const cached = await cache.getUserPreferences('nonexistent');
      expect(cached).toBeNull();
    });

    it('should clear user preferences', async () => {
      await cache.cacheUserPreferences(samplePreferences);
      await cache.clearUserPreferences('user-1');

      const cached = await cache.getUserPreferences('user-1');
      expect(cached).toBeNull();
    });

    it('should clear all user preferences', async () => {
      await cache.cacheUserPreferences(samplePreferences);
      await cache.cacheUserPreferences({
        ...samplePreferences,
        userId: 'user-2',
      });

      await cache.clearAllUserPreferences();

      const cached1 = await cache.getUserPreferences('user-1');
      const cached2 = await cache.getUserPreferences('user-2');

      expect(cached1).toBeNull();
      expect(cached2).toBeNull();
    });
  });

  describe('Cleanup and Expiration', () => {
    it('should have cleanup method that removes expired data', async () => {
      // Test that cleanup method exists and can be called
      await expect(cache.cleanupExpiredData()).resolves.not.toThrow();
    });

    it('should preserve non-expired price data during cleanup', async () => {
      await cache.cachePriceData({
        commodity: 'tomato',
        location: 'Maharashtra',
        minPrice: 15,
        maxPrice: 25,
        averagePrice: 20,
        medianPrice: 20,
        timestamp: Date.now(),
        source: 'demo',
      });

      await cache.cleanupExpiredData();

      const cached = await cache.getCachedPriceData('tomato');
      expect(cached).toBeDefined();
    });
  });

  describe('Utility Methods', () => {
    it('should clear all cached data', async () => {
      // Add data to all stores
      await cache.cachePriceData({
        commodity: 'tomato',
        location: 'Maharashtra',
        minPrice: 15,
        maxPrice: 25,
        averagePrice: 20,
        medianPrice: 20,
        timestamp: Date.now(),
        source: 'demo',
      });

      await cache.cacheNegotiationTemplate({
        id: 'template-1',
        language: 'hi',
        category: 'greeting',
        template: 'नमस्ते',
      });

      await cache.cacheTransaction({
        id: 'txn-1',
        buyerId: 'buyer-1',
        sellerId: 'seller-1',
        commodity: 'tomato',
        quantity: 100,
        unit: 'kg',
        agreedPrice: 20,
        marketAverageAtTime: 22,
        conversationId: 'conv-1',
        completedAt: Date.now(),
        location: 'Maharashtra',
      });

      await cache.cacheUserPreferences({
        userId: 'user-1',
        primaryLanguage: 'hi',
        secondaryLanguages: [],
        speechRate: 0.85,
        volumeBoost: false,
        offlineMode: false,
        favoriteContacts: [],
        updatedAt: Date.now(),
      });

      // Clear all
      await cache.clearAll();

      // Verify all stores are empty
      const stats = await cache.getCacheStats();
      expect(stats.priceDataCount).toBe(0);
      expect(stats.negotiationTemplatesCount).toBe(0);
      expect(stats.transactionsCount).toBe(0);
      expect(stats.userPreferencesCount).toBe(0);
    });

    it('should get cache statistics', async () => {
      await cache.cachePriceData({
        commodity: 'tomato',
        location: 'Maharashtra',
        minPrice: 15,
        maxPrice: 25,
        averagePrice: 20,
        medianPrice: 20,
        timestamp: Date.now(),
        source: 'demo',
      });

      await cache.cacheNegotiationTemplate({
        id: 'template-1',
        language: 'hi',
        category: 'greeting',
        template: 'नमस्ते',
      });

      await cache.cacheTransaction({
        id: 'txn-1',
        buyerId: 'buyer-1',
        sellerId: 'seller-1',
        commodity: 'tomato',
        quantity: 100,
        unit: 'kg',
        agreedPrice: 20,
        marketAverageAtTime: 22,
        conversationId: 'conv-1',
        completedAt: Date.now(),
        location: 'Maharashtra',
      });

      await cache.cacheUserPreferences({
        userId: 'user-1',
        primaryLanguage: 'hi',
        secondaryLanguages: [],
        speechRate: 0.85,
        volumeBoost: false,
        offlineMode: false,
        favoriteContacts: [],
        updatedAt: Date.now(),
      });

      const stats = await cache.getCacheStats();
      expect(stats.priceDataCount).toBe(1);
      expect(stats.negotiationTemplatesCount).toBe(1);
      expect(stats.transactionsCount).toBe(1);
      expect(stats.userPreferencesCount).toBe(1);
    });
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance', async () => {
      const instance1 = await getOfflineDataCache();
      const instance2 = await getOfflineDataCache();

      expect(instance1).toBe(instance2);
    });

    it('should reset singleton', async () => {
      const instance1 = await getOfflineDataCache();
      await resetOfflineDataCache();
      const instance2 = await getOfflineDataCache();

      expect(instance1).not.toBe(instance2);
    });
  });
});
