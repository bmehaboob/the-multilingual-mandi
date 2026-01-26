/**
 * Unit Tests for useOfflineDataCache Hook
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useOfflineDataCache } from './useOfflineDataCache';
import { resetOfflineDataCache } from './OfflineDataCache';

// Mock IndexedDB
import 'fake-indexeddb/auto';

describe('useOfflineDataCache', () => {
  beforeEach(async () => {
    await resetOfflineDataCache();
  });

  afterEach(async () => {
    await resetOfflineDataCache();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      expect(result.current.isInitialized).toBe(false);

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Price Data Methods', () => {
    it('should cache and retrieve price data', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const priceData = {
        commodity: 'tomato',
        location: 'Maharashtra',
        minPrice: 15,
        maxPrice: 25,
        averagePrice: 20,
        medianPrice: 20,
        timestamp: Date.now(),
        source: 'demo' as const,
      };

      await act(async () => {
        await result.current.cachePriceData(priceData);
      });

      let cached;
      await act(async () => {
        cached = await result.current.getCachedPriceData('tomato');
      });

      expect(cached).toBeDefined();
      expect(cached?.commodity).toBe('tomato');
      expect(cached?.averagePrice).toBe(20);
    });

    it('should get all cached price data', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current.cachePriceData({
          commodity: 'tomato',
          location: 'Maharashtra',
          minPrice: 15,
          maxPrice: 25,
          averagePrice: 20,
          medianPrice: 20,
          timestamp: Date.now(),
          source: 'demo',
        });

        await result.current.cachePriceData({
          commodity: 'onion',
          location: 'Maharashtra',
          minPrice: 20,
          maxPrice: 30,
          averagePrice: 25,
          medianPrice: 25,
          timestamp: Date.now(),
          source: 'demo',
        });
      });

      let allData;
      await act(async () => {
        allData = await result.current.getAllCachedPriceData();
      });

      expect(allData).toHaveLength(2);
    });
  });

  describe('Negotiation Template Methods', () => {
    it('should cache and retrieve negotiation template', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const template = {
        id: 'template-1',
        language: 'hi',
        category: 'greeting' as const,
        template: 'नमस्ते {name}',
      };

      await act(async () => {
        await result.current.cacheNegotiationTemplate(template);
      });

      let cached;
      await act(async () => {
        cached = await result.current.getNegotiationTemplate('template-1');
      });

      expect(cached).toBeDefined();
      expect(cached?.language).toBe('hi');
      expect(cached?.category).toBe('greeting');
    });

    it('should cache multiple templates', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const templates = [
        {
          id: 'template-1',
          language: 'hi',
          category: 'greeting' as const,
          template: 'नमस्ते',
        },
        {
          id: 'template-2',
          language: 'hi',
          category: 'counter_offer' as const,
          template: 'क्या आप {price} रुपये में बेच सकते हैं?',
        },
      ];

      await act(async () => {
        await result.current.cacheNegotiationTemplates(templates);
      });

      let hindiTemplates;
      await act(async () => {
        hindiTemplates = await result.current.getNegotiationTemplatesByLanguage('hi');
      });

      expect(hindiTemplates).toHaveLength(2);
    });

    it('should get templates by category', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current.cacheNegotiationTemplates([
          {
            id: 'template-1',
            language: 'hi',
            category: 'greeting',
            template: 'नमस्ते',
          },
          {
            id: 'template-2',
            language: 'te',
            category: 'greeting',
            template: 'నమస్కారం',
          },
        ]);
      });

      let greetingTemplates;
      await act(async () => {
        greetingTemplates = await result.current.getNegotiationTemplatesByCategory('greeting');
      });

      expect(greetingTemplates).toHaveLength(2);
    });
  });

  describe('Transaction Methods', () => {
    it('should cache and retrieve transaction', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const transaction = {
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

      await act(async () => {
        await result.current.cacheTransaction(transaction);
      });

      let cached;
      await act(async () => {
        cached = await result.current.getTransaction('txn-1');
      });

      expect(cached).toBeDefined();
      expect(cached?.commodity).toBe('tomato');
      expect(cached?.agreedPrice).toBe(20);
    });

    it('should get recent transactions', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const now = Date.now();

      await act(async () => {
        for (let i = 0; i < 7; i++) {
          await result.current.cacheTransaction({
            id: `txn-${i}`,
            buyerId: 'buyer-1',
            sellerId: 'seller-1',
            commodity: 'tomato',
            quantity: 100,
            unit: 'kg',
            agreedPrice: 20,
            marketAverageAtTime: 22,
            conversationId: 'conv-1',
            completedAt: now - i * 1000,
            location: 'Maharashtra',
          });
        }
      });

      let recentTransactions;
      await act(async () => {
        recentTransactions = await result.current.getRecentTransactions('buyer-1', 5);
      });

      expect(recentTransactions).toHaveLength(5);
      expect(recentTransactions?.[0].id).toBe('txn-0');
    });
  });

  describe('User Preferences Methods', () => {
    it('should cache and retrieve user preferences', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      const preferences = {
        userId: 'user-1',
        primaryLanguage: 'hi',
        secondaryLanguages: ['en', 'te'],
        speechRate: 0.85,
        volumeBoost: true,
        offlineMode: false,
        favoriteContacts: ['user-2'],
        updatedAt: Date.now(),
      };

      await act(async () => {
        await result.current.cacheUserPreferences(preferences);
      });

      let cached;
      await act(async () => {
        cached = await result.current.getUserPreferences('user-1');
      });

      expect(cached).toBeDefined();
      expect(cached?.primaryLanguage).toBe('hi');
      expect(cached?.speechRate).toBe(0.85);
    });

    it('should update user preferences', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current.cacheUserPreferences({
          userId: 'user-1',
          primaryLanguage: 'hi',
          secondaryLanguages: [],
          speechRate: 0.85,
          volumeBoost: false,
          offlineMode: false,
          favoriteContacts: [],
          updatedAt: Date.now(),
        });

        await result.current.updateUserPreferences('user-1', {
          speechRate: 1.0,
          volumeBoost: true,
        });
      });

      let cached;
      await act(async () => {
        cached = await result.current.getUserPreferences('user-1');
      });

      expect(cached?.speechRate).toBe(1.0);
      expect(cached?.volumeBoost).toBe(true);
      expect(cached?.primaryLanguage).toBe('hi'); // Should remain unchanged
    });
  });

  describe('Utility Methods', () => {
    it('should get cache statistics', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current.cachePriceData({
          commodity: 'tomato',
          location: 'Maharashtra',
          minPrice: 15,
          maxPrice: 25,
          averagePrice: 20,
          medianPrice: 20,
          timestamp: Date.now(),
          source: 'demo',
        });

        await result.current.cacheNegotiationTemplate({
          id: 'template-1',
          language: 'hi',
          category: 'greeting',
          template: 'नमस्ते',
        });

        await result.current.cacheTransaction({
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

        await result.current.cacheUserPreferences({
          userId: 'user-1',
          primaryLanguage: 'hi',
          secondaryLanguages: [],
          speechRate: 0.85,
          volumeBoost: false,
          offlineMode: false,
          favoriteContacts: [],
          updatedAt: Date.now(),
        });
      });

      let stats;
      await act(async () => {
        stats = await result.current.getCacheStats();
      });

      expect(stats?.priceDataCount).toBe(1);
      expect(stats?.negotiationTemplatesCount).toBe(1);
      expect(stats?.transactionsCount).toBe(1);
      expect(stats?.userPreferencesCount).toBe(1);
    });

    it('should clear all cached data', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      await act(async () => {
        await result.current.cachePriceData({
          commodity: 'tomato',
          location: 'Maharashtra',
          minPrice: 15,
          maxPrice: 25,
          averagePrice: 20,
          medianPrice: 20,
          timestamp: Date.now(),
          source: 'demo',
        });

        await result.current.clearAll();
      });

      let stats;
      await act(async () => {
        stats = await result.current.getCacheStats();
      });

      expect(stats?.priceDataCount).toBe(0);
    });
  });

  describe('Error Handling', () => {
    it('should throw error when calling methods before initialization', async () => {
      const { result } = renderHook(() => useOfflineDataCache());

      // Try to call method before initialization
      await expect(
        result.current.cachePriceData({
          commodity: 'tomato',
          location: 'Maharashtra',
          minPrice: 15,
          maxPrice: 25,
          averagePrice: 20,
          medianPrice: 20,
          timestamp: Date.now(),
          source: 'demo',
        })
      ).rejects.toThrow('Cache not initialized');
    });
  });
});
