/**
 * Offline Data Cache Manager
 * 
 * Manages offline caching of data using IndexedDB with TTL support
 * Requirements: 12.2, 12.5, 12.6, 12.8
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';

/**
 * Price data structure
 */
export interface CachedPriceData {
  commodity: string;
  location: string;
  minPrice: number;
  maxPrice: number;
  averagePrice: number;
  medianPrice: number;
  timestamp: number;
  expiresAt: number;
  source: 'enam' | 'mandi_board' | 'crowd_sourced' | 'demo';
}

/**
 * Negotiation template structure
 */
export interface NegotiationTemplate {
  id: string;
  language: string;
  category: 'greeting' | 'counter_offer' | 'acceptance' | 'rejection' | 'closing';
  template: string;
  culturalContext?: string;
}

/**
 * Transaction record structure
 */
export interface TransactionRecord {
  id: string;
  buyerId: string;
  sellerId: string;
  commodity: string;
  quantity: number;
  unit: string;
  agreedPrice: number;
  marketAverageAtTime: number;
  conversationId: string;
  completedAt: number;
  location: string;
}

/**
 * User preferences structure
 */
export interface UserPreferences {
  userId: string;
  primaryLanguage: string;
  secondaryLanguages: string[];
  speechRate: number;
  volumeBoost: boolean;
  offlineMode: boolean;
  favoriteContacts: string[];
  updatedAt: number;
}

/**
 * IndexedDB Schema for offline data cache
 */
interface OfflineDataCacheDB extends DBSchema {
  priceData: {
    key: string; // commodity:location
    value: CachedPriceData;
    indexes: {
      'by-commodity': string;
      'by-expiry': number;
    };
  };
  negotiationTemplates: {
    key: string; // id
    value: NegotiationTemplate;
    indexes: {
      'by-language': string;
      'by-category': string;
    };
  };
  transactions: {
    key: string; // id
    value: TransactionRecord;
    indexes: {
      'by-buyer': string;
      'by-seller': string;
      'by-commodity': string;
      'by-date': number;
    };
  };
  userPreferences: {
    key: string; // userId
    value: UserPreferences;
  };
}

const DB_NAME = 'multilingual-mandi-cache';
const DB_VERSION = 1;

// TTL constants
const PRICE_DATA_TTL = 24 * 60 * 60 * 1000; // 24 hours (Requirement 12.2)
const TRANSACTION_RETENTION = 90 * 24 * 60 * 60 * 1000; // 90 days (Requirement 13.4)

/**
 * OfflineDataCache
 * 
 * Manages offline caching of various data types with TTL support
 * Requirement 12.2: Cache price data with 24-hour TTL
 * Requirement 12.5: Store user preferences locally
 * Requirement 12.6: Cache negotiation templates locally
 * Requirement 12.8: Allow browsing cached transaction history offline
 */
export class OfflineDataCache {
  private db: IDBPDatabase<OfflineDataCacheDB> | null = null;
  private cleanupInterval: number | null = null;

  /**
   * Initialize the offline data cache
   */
  async initialize(options?: { enableAutoCleanup?: boolean }): Promise<void> {
    this.db = await openDB<OfflineDataCacheDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Create price data store
        if (!db.objectStoreNames.contains('priceData')) {
          const priceStore = db.createObjectStore('priceData', { keyPath: 'commodity' });
          priceStore.createIndex('by-commodity', 'commodity');
          priceStore.createIndex('by-expiry', 'expiresAt');
        }

        // Create negotiation templates store
        if (!db.objectStoreNames.contains('negotiationTemplates')) {
          const templateStore = db.createObjectStore('negotiationTemplates', { keyPath: 'id' });
          templateStore.createIndex('by-language', 'language');
          templateStore.createIndex('by-category', 'category');
        }

        // Create transactions store
        if (!db.objectStoreNames.contains('transactions')) {
          const transactionStore = db.createObjectStore('transactions', { keyPath: 'id' });
          transactionStore.createIndex('by-buyer', 'buyerId');
          transactionStore.createIndex('by-seller', 'sellerId');
          transactionStore.createIndex('by-commodity', 'commodity');
          transactionStore.createIndex('by-date', 'completedAt');
        }

        // Create user preferences store
        if (!db.objectStoreNames.contains('userPreferences')) {
          db.createObjectStore('userPreferences', { keyPath: 'userId' });
        }
      },
    });

    // Start periodic cleanup of expired data (enabled by default, disabled in tests)
    if (options?.enableAutoCleanup !== false) {
      this.startCleanupInterval();
    }

    console.log('OfflineDataCache initialized');
  }

  /**
   * Start periodic cleanup of expired data
   */
  private startCleanupInterval(): void {
    // Run cleanup every hour
    this.cleanupInterval = window.setInterval(() => {
      this.cleanupExpiredData().catch((error) => {
        console.error('Cleanup failed:', error);
      });
    }, 60 * 60 * 1000);
  }

  /**
   * Clean up expired data
   */
  async cleanupExpiredData(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const now = Date.now();

    // Clean up expired price data
    const priceData = await this.db.getAll('priceData');
    for (const price of priceData) {
      if (price.expiresAt < now) {
        await this.db.delete('priceData', price.commodity);
        console.log(`Expired price data removed: ${price.commodity}`);
      }
    }

    // Clean up old transactions (older than 90 days)
    const transactions = await this.db.getAll('transactions');
    const cutoffDate = now - TRANSACTION_RETENTION;
    for (const transaction of transactions) {
      if (transaction.completedAt < cutoffDate) {
        await this.db.delete('transactions', transaction.id);
        console.log(`Old transaction removed: ${transaction.id}`);
      }
    }

    console.log('Cleanup completed');
  }

  // ==================== Price Data Methods ====================

  /**
   * Cache price data with 24-hour TTL
   * Requirement 12.2: Cache price data with 24-hour TTL
   */
  async cachePriceData(priceData: Omit<CachedPriceData, 'expiresAt'>): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const cachedData: CachedPriceData = {
      ...priceData,
      expiresAt: Date.now() + PRICE_DATA_TTL,
    };

    await this.db.put('priceData', cachedData);
    console.log(`Price data cached: ${priceData.commodity} at ${priceData.location}`);
  }

  /**
   * Get cached price data
   * Returns null if not found or expired
   */
  async getCachedPriceData(commodity: string): Promise<CachedPriceData | null> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const data = await this.db.get('priceData', commodity);

    if (!data) {
      return null;
    }

    // Check if expired
    if (data.expiresAt < Date.now()) {
      await this.db.delete('priceData', commodity);
      console.log(`Expired price data removed: ${commodity}`);
      return null;
    }

    return data;
  }

  /**
   * Get all cached price data (non-expired)
   */
  async getAllCachedPriceData(): Promise<CachedPriceData[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const allData = await this.db.getAll('priceData');
    const now = Date.now();

    // Filter out expired data
    return allData.filter(data => data.expiresAt >= now);
  }

  /**
   * Clear all price data
   */
  async clearPriceData(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.clear('priceData');
    console.log('All price data cleared');
  }

  // ==================== Negotiation Template Methods ====================

  /**
   * Cache negotiation template
   * Requirement 12.6: Cache negotiation templates locally
   */
  async cacheNegotiationTemplate(template: NegotiationTemplate): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.put('negotiationTemplates', template);
    console.log(`Negotiation template cached: ${template.id}`);
  }

  /**
   * Cache multiple negotiation templates
   */
  async cacheNegotiationTemplates(templates: NegotiationTemplate[]): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const tx = this.db.transaction('negotiationTemplates', 'readwrite');
    await Promise.all([
      ...templates.map(template => tx.store.put(template)),
      tx.done,
    ]);

    console.log(`${templates.length} negotiation templates cached`);
  }

  /**
   * Get negotiation template by ID
   */
  async getNegotiationTemplate(id: string): Promise<NegotiationTemplate | null> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const template = await this.db.get('negotiationTemplates', id);
    return template || null;
  }

  /**
   * Get negotiation templates by language
   */
  async getNegotiationTemplatesByLanguage(language: string): Promise<NegotiationTemplate[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAllFromIndex('negotiationTemplates', 'by-language', language);
  }

  /**
   * Get negotiation templates by category
   */
  async getNegotiationTemplatesByCategory(
    category: NegotiationTemplate['category']
  ): Promise<NegotiationTemplate[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAllFromIndex('negotiationTemplates', 'by-category', category);
  }

  /**
   * Get all negotiation templates
   */
  async getAllNegotiationTemplates(): Promise<NegotiationTemplate[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAll('negotiationTemplates');
  }

  /**
   * Clear all negotiation templates
   */
  async clearNegotiationTemplates(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.clear('negotiationTemplates');
    console.log('All negotiation templates cleared');
  }

  // ==================== Transaction Methods ====================

  /**
   * Cache transaction record
   * Requirement 12.8: Cache transaction history for offline access
   */
  async cacheTransaction(transaction: TransactionRecord): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.put('transactions', transaction);
    console.log(`Transaction cached: ${transaction.id}`);
  }

  /**
   * Get transaction by ID
   */
  async getTransaction(id: string): Promise<TransactionRecord | null> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const transaction = await this.db.get('transactions', id);
    return transaction || null;
  }

  /**
   * Get transactions by buyer ID
   */
  async getTransactionsByBuyer(buyerId: string): Promise<TransactionRecord[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAllFromIndex('transactions', 'by-buyer', buyerId);
  }

  /**
   * Get transactions by seller ID
   */
  async getTransactionsBySeller(sellerId: string): Promise<TransactionRecord[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAllFromIndex('transactions', 'by-seller', sellerId);
  }

  /**
   * Get transactions by commodity
   */
  async getTransactionsByCommodity(commodity: string): Promise<TransactionRecord[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAllFromIndex('transactions', 'by-commodity', commodity);
  }

  /**
   * Get recent transactions (last N transactions)
   * Requirement 13.3: Read out last 5 transactions
   */
  async getRecentTransactions(userId: string, limit: number = 5): Promise<TransactionRecord[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    // Get all transactions for the user (as buyer or seller)
    const buyerTransactions = await this.getTransactionsByBuyer(userId);
    const sellerTransactions = await this.getTransactionsBySeller(userId);

    // Combine and sort by date (most recent first)
    const allTransactions = [...buyerTransactions, ...sellerTransactions];
    allTransactions.sort((a, b) => b.completedAt - a.completedAt);

    // Return the most recent N transactions
    return allTransactions.slice(0, limit);
  }

  /**
   * Get all transactions
   */
  async getAllTransactions(): Promise<TransactionRecord[]> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    return this.db.getAll('transactions');
  }

  /**
   * Clear all transactions
   */
  async clearTransactions(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.clear('transactions');
    console.log('All transactions cleared');
  }

  // ==================== User Preferences Methods ====================

  /**
   * Cache user preferences
   * Requirement 12.5: Store user preferences locally
   */
  async cacheUserPreferences(preferences: UserPreferences): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const updatedPreferences: UserPreferences = {
      ...preferences,
      updatedAt: Date.now(),
    };

    await this.db.put('userPreferences', updatedPreferences);
    console.log(`User preferences cached: ${preferences.userId}`);
  }

  /**
   * Get user preferences
   */
  async getUserPreferences(userId: string): Promise<UserPreferences | null> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const preferences = await this.db.get('userPreferences', userId);
    return preferences || null;
  }

  /**
   * Update user preferences (partial update)
   */
  async updateUserPreferences(
    userId: string,
    updates: Partial<Omit<UserPreferences, 'userId' | 'updatedAt'>>
  ): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const existing = await this.getUserPreferences(userId);
    if (!existing) {
      throw new Error(`User preferences not found: ${userId}`);
    }

    const updated: UserPreferences = {
      ...existing,
      ...updates,
      updatedAt: Date.now(),
    };

    await this.db.put('userPreferences', updated);
    console.log(`User preferences updated: ${userId}`);
  }

  /**
   * Clear user preferences
   */
  async clearUserPreferences(userId: string): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.delete('userPreferences', userId);
    console.log(`User preferences cleared: ${userId}`);
  }

  /**
   * Clear all user preferences
   */
  async clearAllUserPreferences(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await this.db.clear('userPreferences');
    console.log('All user preferences cleared');
  }

  // ==================== Utility Methods ====================

  /**
   * Clear all cached data
   */
  async clearAll(): Promise<void> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    await Promise.all([
      this.clearPriceData(),
      this.clearNegotiationTemplates(),
      this.clearTransactions(),
      this.clearAllUserPreferences(),
    ]);

    console.log('All cached data cleared');
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<{
    priceDataCount: number;
    negotiationTemplatesCount: number;
    transactionsCount: number;
    userPreferencesCount: number;
  }> {
    if (!this.db) {
      throw new Error('OfflineDataCache not initialized');
    }

    const [priceData, templates, transactions, preferences] = await Promise.all([
      this.getAllCachedPriceData(),
      this.getAllNegotiationTemplates(),
      this.getAllTransactions(),
      this.db.getAll('userPreferences'),
    ]);

    return {
      priceDataCount: priceData.length,
      negotiationTemplatesCount: templates.length,
      transactionsCount: transactions.length,
      userPreferencesCount: preferences.length,
    };
  }

  /**
   * Clean up resources
   */
  async destroy(): Promise<void> {
    if (this.cleanupInterval !== null) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }

    if (this.db) {
      this.db.close();
      this.db = null;
    }

    console.log('OfflineDataCache destroyed');
  }
}

// Singleton instance
let offlineDataCacheInstance: OfflineDataCache | null = null;

/**
 * Get the singleton instance of OfflineDataCache
 */
export async function getOfflineDataCache(): Promise<OfflineDataCache> {
  if (!offlineDataCacheInstance) {
    offlineDataCacheInstance = new OfflineDataCache();
    await offlineDataCacheInstance.initialize();
  }
  return offlineDataCacheInstance;
}

/**
 * Reset the singleton instance (useful for testing)
 */
export async function resetOfflineDataCache(): Promise<void> {
  if (offlineDataCacheInstance) {
    await offlineDataCacheInstance.destroy();
    offlineDataCacheInstance = null;
  }
}
