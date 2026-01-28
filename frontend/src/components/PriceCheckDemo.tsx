/**
 * Price Check Demo Component
 * 
 * Demonstrates the PriceCheckUI component with backend API integration.
 * Shows voice-activated price queries and price comparison functionality.
 * 
 * Requirements: 6.3, 7.5
 */

import React, { useState } from 'react';
import { PriceCheckUI, PriceAggregation, PriceAnalysis } from './PriceCheckUI';
import { queryPrice, comparePrice } from '../services/api/priceApi';

export const PriceCheckDemo: React.FC = () => {
  const [language, setLanguage] = useState('en');
  const [userLocation, setUserLocation] = useState({
    state: 'Maharashtra',
    district: 'Pune',
  });

  /**
   * Handle price query
   */
  const handlePriceQuery = async (
    commodity: string,
    location: any
  ): Promise<PriceAggregation> => {
    try {
      const result = await queryPrice({
        commodity,
        state: location.state,
        district: location.district,
      });
      return result;
    } catch (error) {
      console.error('Price query failed:', error);
      throw error;
    }
  };

  /**
   * Handle price comparison
   */
  const handlePriceComparison = async (
    commodity: string,
    quotedPrice: number,
    marketData: PriceAggregation
  ): Promise<PriceAnalysis> => {
    try {
      const result = await comparePrice({
        commodity,
        quoted_price: quotedPrice,
        state: marketData.location.state,
        district: marketData.location.district,
      });
      return result.analysis;
    } catch (error) {
      console.error('Price comparison failed:', error);
      throw error;
    }
  };

  return (
    <div style={styles.container}>
      {/* Demo Controls */}
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>Language:</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={styles.select}
          >
            <option value="en">English</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="te">తెలుగు (Telugu)</option>
            <option value="ta">தமிழ் (Tamil)</option>
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>State:</label>
          <select
            value={userLocation.state}
            onChange={(e) =>
              setUserLocation({ ...userLocation, state: e.target.value })
            }
            style={styles.select}
          >
            <option value="Maharashtra">Maharashtra</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Andhra Pradesh">Andhra Pradesh</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Punjab">Punjab</option>
          </select>
        </div>
      </div>

      {/* Price Check UI */}
      <PriceCheckUI
        language={language}
        userLocation={userLocation}
        onPriceQuery={handlePriceQuery}
        onPriceComparison={handlePriceComparison}
      />

      {/* Instructions */}
      <div style={styles.instructions}>
        <h3 style={styles.instructionsTitle}>How to Use:</h3>
        <ol style={styles.instructionsList}>
          <li>Enter a commodity name (e.g., "tomato", "onion", "rice")</li>
          <li>Optionally enter a quoted price to compare against market average</li>
          <li>Click "Check Price" to query current market prices</li>
          <li>View price comparison results with data source indicators</li>
          <li>Listen to voice output of price information (if TTS is enabled)</li>
        </ol>

        <div style={styles.note}>
          <strong>Note:</strong> This demo uses realistic demo data for development.
          Data sources are clearly indicated (eNAM, Mandi Board, User Data, or Demo Data).
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  controls: {
    display: 'flex',
    gap: '20px',
    padding: '20px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #ddd',
    flexWrap: 'wrap',
  },
  controlGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  select: {
    padding: '8px 12px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    backgroundColor: '#fff',
    cursor: 'pointer',
  },
  instructions: {
    maxWidth: '800px',
    margin: '20px auto',
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  instructionsTitle: {
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#333',
  },
  instructionsList: {
    margin: '0 0 16px 0',
    paddingLeft: '24px',
    lineHeight: '1.8',
    color: '#555',
  },
  note: {
    padding: '12px',
    backgroundColor: '#e3f2fd',
    borderLeft: '4px solid #2196f3',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#1565c0',
  },
};

export default PriceCheckDemo;
