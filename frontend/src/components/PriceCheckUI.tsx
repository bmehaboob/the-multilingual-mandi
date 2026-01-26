/**
 * Price Check UI Component
 * 
 * Voice-activated price queries with visual display and voice output.
 * Shows price comparison results and data source indicators.
 * 
 * Requirements: 6.3, 7.5
 */

import React, { useState, useCallback } from 'react';
import { useVoiceCommands } from '../services/voice/useVoiceCommands';
import { useAudioFeedback } from '../services/audio/useAudioFeedback';

// Types
export interface PriceData {
  id: string;
  commodity: string;
  price: number;
  unit: string;
  source: 'enam' | 'mandi_board' | 'crowd_sourced' | 'demo';
  location: {
    state: string;
    district?: string;
  };
  mandi_name?: string;
  timestamp: string;
  is_demo: boolean;
}

export interface PriceAggregation {
  commodity: string;
  location: {
    state: string;
    district?: string;
  };
  min_price: number;
  max_price: number;
  average_price: number;
  median_price: number;
  std_dev: number;
  sample_size: number;
  timestamp: string;
  sources_used: string[];
}

export interface PriceAnalysis {
  verdict: 'fair' | 'high' | 'low' | 'slightly_high' | 'slightly_low';
  message: string;
  percentage_difference: number;
  market_average: number;
  quoted_price: number;
}

export interface PriceCheckUIProps {
  language: string;
  userLocation?: {
    state: string;
    district?: string;
  };
  onPriceQuery?: (commodity: string, location: any) => Promise<PriceAggregation>;
  onPriceComparison?: (commodity: string, quotedPrice: number, marketData: PriceAggregation) => Promise<PriceAnalysis>;
}

type QueryState = 'idle' | 'listening' | 'processing' | 'displaying' | 'error';

/**
 * Data source labels in different languages
 */
const SOURCE_LABELS: Record<string, Record<string, string>> = {
  hi: {
    enam: 'ई-नाम',
    mandi_board: 'मंडी बोर्ड',
    crowd_sourced: 'उपयोगकर्ता डेटा',
    demo: 'डेमो डेटा',
  },
  en: {
    enam: 'eNAM',
    mandi_board: 'Mandi Board',
    crowd_sourced: 'User Data',
    demo: 'Demo Data',
  },
  te: {
    enam: 'ఈ-నామ్',
    mandi_board: 'మండి బోర్డ్',
    crowd_sourced: 'వినియోగదారు డేటా',
    demo: 'డెమో డేటా',
  },
  ta: {
    enam: 'ஈ-நாம்',
    mandi_board: 'மண்டி வாரியம்',
    crowd_sourced: 'பயனர் தரவு',
    demo: 'டெமோ தரவு',
  },
};

/**
 * UI labels in different languages
 */
const UI_LABELS: Record<string, Record<string, string>> = {
  hi: {
    title: 'मूल्य जांच',
    checkPrice: 'मूल्य जांचें',
    commodity: 'वस्तु',
    quotedPrice: 'उद्धृत मूल्य',
    marketAverage: 'बाजार औसत',
    priceRange: 'मूल्य सीमा',
    sources: 'डेटा स्रोत',
    enterCommodity: 'वस्तु का नाम दर्ज करें',
    enterPrice: 'मूल्य दर्ज करें (वैकल्पिक)',
    processing: 'प्रसंस्करण...',
    error: 'त्रुटि',
    noData: 'कोई डेटा उपलब्ध नहीं',
  },
  en: {
    title: 'Price Check',
    checkPrice: 'Check Price',
    commodity: 'Commodity',
    quotedPrice: 'Quoted Price',
    marketAverage: 'Market Average',
    priceRange: 'Price Range',
    sources: 'Data Sources',
    enterCommodity: 'Enter commodity name',
    enterPrice: 'Enter price (optional)',
    processing: 'Processing...',
    error: 'Error',
    noData: 'No data available',
  },
  te: {
    title: 'ధర తనిఖీ',
    checkPrice: 'ధర తనిఖీ చేయండి',
    commodity: 'వస్తువు',
    quotedPrice: 'కోట్ చేసిన ధర',
    marketAverage: 'మార్కెట్ సగటు',
    priceRange: 'ధర పరిధి',
    sources: 'డేటా మూలాలు',
    enterCommodity: 'వస్తువు పేరు నమోదు చేయండి',
    enterPrice: 'ధర నమోదు చేయండి (ఐచ్ఛికం)',
    processing: 'ప్రాసెస్ చేస్తోంది...',
    error: 'లోపం',
    noData: 'డేటా అందుబాటులో లేదు',
  },
  ta: {
    title: 'விலை சரிபார்ப்பு',
    checkPrice: 'விலை சரிபார்க்கவும்',
    commodity: 'பொருள்',
    quotedPrice: 'மேற்கோள் விலை',
    marketAverage: 'சந்தை சராசரி',
    priceRange: 'விலை வரம்பு',
    sources: 'தரவு மூலங்கள்',
    enterCommodity: 'பொருளின் பெயரை உள்ளிடவும்',
    enterPrice: 'விலையை உள்ளிடவும் (விருப்பமானது)',
    processing: 'செயலாக்கம்...',
    error: 'பிழை',
    noData: 'தரவு கிடைக்கவில்லை',
  },
};

/**
 * Price Check UI Component
 */
export const PriceCheckUI: React.FC<PriceCheckUIProps> = ({
  language,
  userLocation,
  onPriceQuery,
  onPriceComparison,
}) => {
  // State
  const [commodity, setCommodity] = useState('');
  const [quotedPrice, setQuotedPrice] = useState('');
  const [queryState, setQueryState] = useState<QueryState>('idle');
  const [priceData, setPriceData] = useState<PriceAggregation | null>(null);
  const [priceAnalysis, setPriceAnalysis] = useState<PriceAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Hooks
  const audioFeedback = useAudioFeedback({
    language,
    enabled: true,
    volume: 0.7,
    useTTS: true,
  });

  const voiceCommands = useVoiceCommands({
    language,
    confirmationRequired: true,
    onCommandExecuted: handleVoiceCommand,
  });

  /**
   * Handle voice commands
   */
  function handleVoiceCommand(command: any) {
    switch (command.action) {
      case 'check_price':
        if (command.parameters?.commodity) {
          setCommodity(command.parameters.commodity);
          handleCheckPrice(command.parameters.commodity, command.parameters.price);
        }
        break;
      case 'clear':
        handleClear();
        break;
      default:
        break;
    }
  }

  /**
   * Get UI label
   */
  const getLabel = useCallback((key: string): string => {
    const labels = UI_LABELS[language] || UI_LABELS['en'];
    return labels[key] || key;
  }, [language]);

  /**
   * Get source label
   */
  const getSourceLabel = useCallback((source: string): string => {
    const labels = SOURCE_LABELS[language] || SOURCE_LABELS['en'];
    return labels[source] || source;
  }, [language]);

  /**
   * Check price for a commodity (Requirement 6.3)
   */
  const handleCheckPrice = useCallback(async (commodityName?: string, price?: string) => {
    const targetCommodity = commodityName || commodity;
    const targetPrice = price || quotedPrice;

    if (!targetCommodity.trim()) {
      setError('Please enter a commodity name');
      await audioFeedback.playStateFeedback('error', 'Please enter a commodity name');
      return;
    }

    setQueryState('processing');
    setError(null);
    setPriceData(null);
    setPriceAnalysis(null);

    try {
      // Play processing feedback
      await audioFeedback.playStateFeedback('processing', 'Checking prices');

      // Query price data (Requirement 6.3 - within 3 seconds)
      const location = userLocation || { state: 'Maharashtra' };
      
      let marketData: PriceAggregation;
      if (onPriceQuery) {
        marketData = await onPriceQuery(targetCommodity, location);
      } else {
        // Mock data for demo
        marketData = await mockPriceQuery(targetCommodity, location);
      }

      setPriceData(marketData);

      // If quoted price is provided, perform comparison (Requirement 7.5)
      if (targetPrice && parseFloat(targetPrice) > 0) {
        const analysis = await performPriceComparison(
          targetCommodity,
          parseFloat(targetPrice),
          marketData
        );
        setPriceAnalysis(analysis);

        // Provide voice output of comparison result (Requirement 7.5)
        await audioFeedback.playCustomMessage(analysis.message);
      } else {
        // Provide voice output of price range
        const priceMessage = `Current market price for ${targetCommodity} ranges from ${marketData.min_price} to ${marketData.max_price} rupees per kilogram, with an average of ${marketData.average_price} rupees.`;
        await audioFeedback.playCustomMessage(priceMessage);
      }

      setQueryState('displaying');
      await audioFeedback.playStateFeedback('success');
    } catch (err) {
      setQueryState('error');
      const errorMessage = err instanceof Error ? err.message : 'Failed to check price';
      setError(errorMessage);
      await audioFeedback.playStateFeedback('error', errorMessage);
    }
  }, [commodity, quotedPrice, userLocation, audioFeedback, onPriceQuery]);

  /**
   * Perform price comparison
   */
  const performPriceComparison = async (
    commodityName: string,
    price: number,
    marketData: PriceAggregation
  ): Promise<PriceAnalysis> => {
    if (onPriceComparison) {
      return await onPriceComparison(commodityName, price, marketData);
    } else {
      // Mock comparison for demo
      return mockPriceComparison(price, marketData);
    }
  };

  /**
   * Mock price query (for demo purposes)
   */
  const mockPriceQuery = async (
    commodityName: string,
    location: any
  ): Promise<PriceAggregation> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Generate mock data
    const basePrice = 20 + Math.random() * 30;
    const variation = basePrice * 0.1;

    return {
      commodity: commodityName,
      location,
      min_price: parseFloat((basePrice - variation).toFixed(2)),
      max_price: parseFloat((basePrice + variation).toFixed(2)),
      average_price: parseFloat(basePrice.toFixed(2)),
      median_price: parseFloat(basePrice.toFixed(2)),
      std_dev: parseFloat(variation.toFixed(2)),
      sample_size: 3,
      timestamp: new Date().toISOString(),
      sources_used: ['demo'],
    };
  };

  /**
   * Mock price comparison (for demo purposes)
   */
  const mockPriceComparison = (
    price: number,
    marketData: PriceAggregation
  ): PriceAnalysis => {
    const avg = marketData.average_price;
    const percentageDiff = ((price - avg) / avg) * 100;

    let verdict: PriceAnalysis['verdict'];
    let message: string;

    if (Math.abs(price - avg) <= 0.05 * avg) {
      verdict = 'fair';
      message = `Price is fair. The quoted price of ₹${price.toFixed(2)} is close to the market average of ₹${avg.toFixed(2)}.`;
    } else if (price > avg + 0.10 * avg) {
      verdict = 'high';
      message = `Price is high. The quoted price of ₹${price.toFixed(2)} is ${Math.abs(percentageDiff).toFixed(1)}% above the market average of ₹${avg.toFixed(2)}. You may want to negotiate.`;
    } else if (price < avg - 0.10 * avg) {
      verdict = 'low';
      message = `Price is unusually low. The quoted price of ₹${price.toFixed(2)} is ${Math.abs(percentageDiff).toFixed(1)}% below the market average of ₹${avg.toFixed(2)}. This is a good deal, but verify the quality.`;
    } else if (price > avg) {
      verdict = 'slightly_high';
      message = `Price is slightly high. The quoted price of ₹${price.toFixed(2)} is ${Math.abs(percentageDiff).toFixed(1)}% above the market average of ₹${avg.toFixed(2)}.`;
    } else {
      verdict = 'slightly_low';
      message = `Price is slightly low. The quoted price of ₹${price.toFixed(2)} is ${Math.abs(percentageDiff).toFixed(1)}% below the market average of ₹${avg.toFixed(2)}.`;
    }

    return {
      verdict,
      message,
      percentage_difference: percentageDiff,
      market_average: avg,
      quoted_price: price,
    };
  };

  /**
   * Clear the form and results
   */
  const handleClear = useCallback(() => {
    setCommodity('');
    setQuotedPrice('');
    setPriceData(null);
    setPriceAnalysis(null);
    setError(null);
    setQueryState('idle');
  }, []);

  /**
   * Get verdict color
   */
  const getVerdictColor = (verdict: string): string => {
    switch (verdict) {
      case 'fair':
        return '#4caf50';
      case 'high':
        return '#f44336';
      case 'low':
        return '#2196f3';
      case 'slightly_high':
        return '#ff9800';
      case 'slightly_low':
        return '#03a9f4';
      default:
        return '#666';
    }
  };

  /**
   * Get data source badge color
   */
  const getSourceColor = (source: string): string => {
    switch (source) {
      case 'enam':
        return '#4caf50';
      case 'mandi_board':
        return '#2196f3';
      case 'crowd_sourced':
        return '#ff9800';
      case 'demo':
        return '#9e9e9e';
      default:
        return '#666';
    }
  };

  return (
    <div className="price-check-ui" style={styles.container}>
      {/* Header */}
      <div className="price-check-header" style={styles.header}>
        <h2 style={styles.title}>{getLabel('title')}</h2>
      </div>

      {/* Input Form */}
      <div className="price-check-form" style={styles.form}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>{getLabel('commodity')}</label>
          <input
            type="text"
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            placeholder={getLabel('enterCommodity')}
            style={styles.input}
            disabled={queryState === 'processing'}
          />
        </div>

        <div style={styles.inputGroup}>
          <label style={styles.label}>{getLabel('quotedPrice')} (₹/kg)</label>
          <input
            type="number"
            value={quotedPrice}
            onChange={(e) => setQuotedPrice(e.target.value)}
            placeholder={getLabel('enterPrice')}
            style={styles.input}
            disabled={queryState === 'processing'}
            min="0"
            step="0.01"
          />
        </div>

        <div style={styles.buttonGroup}>
          <button
            onClick={() => handleCheckPrice()}
            disabled={queryState === 'processing' || !commodity.trim()}
            style={{
              ...styles.button,
              ...styles.primaryButton,
              opacity: queryState === 'processing' || !commodity.trim() ? 0.5 : 1,
            }}
          >
            {queryState === 'processing' ? getLabel('processing') : getLabel('checkPrice')}
          </button>

          <button
            onClick={handleClear}
            disabled={queryState === 'processing'}
            style={{
              ...styles.button,
              ...styles.secondaryButton,
              opacity: queryState === 'processing' ? 0.5 : 1,
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message" style={styles.error}>
          <span style={styles.errorIcon}>⚠</span>
          {error}
        </div>
      )}

      {/* Price Analysis Result */}
      {priceAnalysis && (
        <div className="price-analysis" style={styles.analysisCard}>
          <div
            className="verdict-badge"
            style={{
              ...styles.verdictBadge,
              backgroundColor: getVerdictColor(priceAnalysis.verdict),
            }}
          >
            {priceAnalysis.verdict.toUpperCase()}
          </div>
          <p style={styles.analysisMessage}>{priceAnalysis.message}</p>
          <div style={styles.analysisDetails}>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>{getLabel('quotedPrice')}:</span>
              <span style={styles.detailValue}>₹{priceAnalysis.quoted_price.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>{getLabel('marketAverage')}:</span>
              <span style={styles.detailValue}>₹{priceAnalysis.market_average.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>Difference:</span>
              <span
                style={{
                  ...styles.detailValue,
                  color: priceAnalysis.percentage_difference > 0 ? '#f44336' : '#4caf50',
                }}
              >
                {priceAnalysis.percentage_difference > 0 ? '+' : ''}
                {priceAnalysis.percentage_difference.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Price Data Display */}
      {priceData && (
        <div className="price-data" style={styles.priceCard}>
          <h3 style={styles.cardTitle}>
            {priceData.commodity} - {priceData.location.state}
          </h3>

          <div style={styles.priceStats}>
            <div style={styles.statItem}>
              <span style={styles.statLabel}>{getLabel('marketAverage')}</span>
              <span style={styles.statValue}>₹{priceData.average_price.toFixed(2)}</span>
              <span style={styles.statUnit}>per kg</span>
            </div>

            <div style={styles.statItem}>
              <span style={styles.statLabel}>{getLabel('priceRange')}</span>
              <span style={styles.statValue}>
                ₹{priceData.min_price.toFixed(2)} - ₹{priceData.max_price.toFixed(2)}
              </span>
              <span style={styles.statUnit}>per kg</span>
            </div>
          </div>

          {/* Data Source Indicators (Requirement 7.5) */}
          <div style={styles.sourcesSection}>
            <span style={styles.sourcesLabel}>{getLabel('sources')}:</span>
            <div style={styles.sourceBadges}>
              {priceData.sources_used.map((source) => (
                <span
                  key={source}
                  className="source-badge"
                  style={{
                    ...styles.sourceBadge,
                    backgroundColor: getSourceColor(source),
                  }}
                >
                  {getSourceLabel(source)}
                </span>
              ))}
            </div>
          </div>

          <div style={styles.metadata}>
            <span style={styles.metadataText}>
              Based on {priceData.sample_size} price points
            </span>
            <span style={styles.metadataText}>
              Updated: {new Date(priceData.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Voice Command Confirmation */}
      {voiceCommands.isWaitingForConfirmation && voiceCommands.confirmationMessage && (
        <div className="confirmation-dialog" style={styles.confirmationDialog}>
          <p style={styles.confirmationText}>{voiceCommands.confirmationMessage}</p>
          <div style={styles.confirmationButtons}>
            <button
              onClick={voiceCommands.confirmPendingCommand}
              style={{ ...styles.button, ...styles.confirmButton }}
            >
              Yes
            </button>
            <button
              onClick={voiceCommands.cancelPendingCommand}
              style={{ ...styles.button, ...styles.cancelButton }}
            >
              No
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Styles
 */
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: '#fafafa',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    minHeight: '100vh',
  },
  header: {
    padding: '16px',
    backgroundColor: '#4caf50',
    color: '#fff',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 'bold',
  },
  form: {
    padding: '20px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #ddd',
  },
  inputGroup: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  input: {
    width: '100%',
    padding: '12px',
    fontSize: '16px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    boxSizing: 'border-box',
  },
  buttonGroup: {
    display: 'flex',
    gap: '12px',
    marginTop: '20px',
  },
  button: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
  primaryButton: {
    flex: 2,
    backgroundColor: '#4caf50',
    color: '#fff',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    color: '#333',
  },
  error: {
    padding: '16px',
    backgroundColor: '#fee',
    color: '#c33',
    borderBottom: '1px solid #fcc',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  errorIcon: {
    fontSize: '20px',
  },
  analysisCard: {
    margin: '20px',
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  verdictBadge: {
    display: 'inline-block',
    padding: '8px 16px',
    borderRadius: '20px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
    marginBottom: '12px',
  },
  analysisMessage: {
    fontSize: '16px',
    lineHeight: '1.5',
    color: '#333',
    marginBottom: '16px',
  },
  analysisDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '16px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
  },
  detailItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: '14px',
    color: '#666',
  },
  detailValue: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
  },
  priceCard: {
    margin: '20px',
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  cardTitle: {
    margin: '0 0 20px 0',
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#333',
  },
  priceStats: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
    marginBottom: '20px',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    padding: '16px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
  },
  statLabel: {
    fontSize: '12px',
    color: '#666',
    marginBottom: '8px',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#4caf50',
    marginBottom: '4px',
  },
  statUnit: {
    fontSize: '12px',
    color: '#999',
  },
  sourcesSection: {
    marginTop: '20px',
    paddingTop: '16px',
    borderTop: '1px solid #eee',
  },
  sourcesLabel: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#666',
    marginBottom: '8px',
    display: 'block',
  },
  sourceBadges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  sourceBadge: {
    padding: '6px 12px',
    borderRadius: '16px',
    color: '#fff',
    fontSize: '12px',
    fontWeight: '500',
  },
  metadata: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #eee',
    display: 'flex',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '8px',
  },
  metadataText: {
    fontSize: '12px',
    color: '#999',
  },
  confirmationDialog: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    maxWidth: '400px',
    width: '90%',
    padding: '16px',
    backgroundColor: '#fff3cd',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    border: '1px solid #ffc107',
  },
  confirmationText: {
    margin: '0 0 12px 0',
    fontSize: '15px',
    fontWeight: '500',
    color: '#333',
  },
  confirmationButtons: {
    display: 'flex',
    gap: '12px',
  },
  confirmButton: {
    flex: 1,
    backgroundColor: '#4caf50',
    color: '#fff',
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#f44336',
    color: '#fff',
  },
};

export default PriceCheckUI;
