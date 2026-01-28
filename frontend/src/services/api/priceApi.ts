/**
 * Price API Service
 * 
 * Provides functions to query prices and perform price comparisons
 * from the backend API.
 * 
 * Requirements: 6.3, 7.5
 */

import { PriceAggregation, PriceAnalysis } from '../../components/PriceCheckUI';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface PriceQueryRequest {
  commodity: string;
  state?: string;
  district?: string;
}

export interface PriceComparisonRequest {
  commodity: string;
  quoted_price: number;
  state?: string;
  district?: string;
}

export interface PriceComparisonResponse {
  verdict: string;
  message: string;
  percentage_difference: number;
  market_average: number;
  quoted_price: number;
  market_data: PriceAggregation;
}

/**
 * Query current market prices for a commodity
 * 
 * Requirement 6.3: Returns price data within 3 seconds
 * 
 * @param request - Price query request
 * @returns Promise with price aggregation data
 */
export async function queryPrice(request: PriceQueryRequest): Promise<PriceAggregation> {
  try {
    const response = await fetch(`${API_BASE_URL}/prices/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to query prices');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Price query error:', error);
    throw error;
  }
}

/**
 * Compare a quoted price against market average
 * 
 * Requirement 7.5: Provides price comparison with detailed analysis
 * 
 * @param request - Price comparison request
 * @returns Promise with price analysis
 */
export async function comparePrice(request: PriceComparisonRequest): Promise<{
  analysis: PriceAnalysis;
  marketData: PriceAggregation;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/prices/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to compare prices');
    }

    const data: PriceComparisonResponse = await response.json();
    
    return {
      analysis: {
        verdict: data.verdict as PriceAnalysis['verdict'],
        message: data.message,
        percentage_difference: data.percentage_difference,
        market_average: data.market_average,
        quoted_price: data.quoted_price,
      },
      marketData: data.market_data,
    };
  } catch (error) {
    console.error('Price comparison error:', error);
    throw error;
  }
}

/**
 * Get list of available commodities
 * 
 * @returns Promise with list of commodity names
 */
export async function listCommodities(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/prices/commodities`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list commodities');
    }

    const data = await response.json();
    return data.commodities;
  } catch (error) {
    console.error('List commodities error:', error);
    throw error;
  }
}
