/**
 * Network Mode Indicator Component
 * 
 * Displays current network mode and allows manual override
 * Requirements: 10.3
 */

import React from 'react';
import { useNetworkSpeed, NetworkMode } from '../services/useNetworkSpeed';
import { NetworkQuality } from '../services/NetworkSpeedDetector';

export interface NetworkModeIndicatorProps {
  /** Whether to show detailed information */
  showDetails?: boolean;
  /** Whether to allow manual mode override */
  allowManualOverride?: boolean;
  /** Custom CSS class */
  className?: string;
}

/**
 * NetworkModeIndicator Component
 * 
 * Displays network speed and mode information
 * Requirement 10.3: Switch to text-only mode when speed < 100 kbps
 */
export const NetworkModeIndicator: React.FC<NetworkModeIndicatorProps> = ({
  showDetails = false,
  allowManualOverride = false,
  className = '',
}) => {
  const {
    speedKbps,
    averageSpeedKbps,
    latencyMs,
    quality,
    mode,
    isTextOnlyMode,
    measureSpeed,
    setMode,
  } = useNetworkSpeed();

  const getQualityColor = (quality: NetworkQuality): string => {
    switch (quality) {
      case 'fast':
        return 'text-green-600';
      case 'moderate':
        return 'text-blue-600';
      case 'slow':
        return 'text-yellow-600';
      case 'very-slow':
        return 'text-orange-600';
      case 'offline':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getQualityIcon = (quality: NetworkQuality): string => {
    switch (quality) {
      case 'fast':
        return '📶';
      case 'moderate':
        return '📶';
      case 'slow':
        return '📶';
      case 'very-slow':
        return '📶';
      case 'offline':
        return '📵';
      default:
        return '📶';
    }
  };

  const getModeLabel = (mode: NetworkMode): string => {
    return mode === 'text-only' ? 'Text-Only Mode' : 'Full Mode';
  };

  const getModeDescription = (mode: NetworkMode): string => {
    if (mode === 'text-only') {
      return 'Audio features disabled to save bandwidth';
    }
    return 'All features enabled';
  };

  const handleToggleMode = () => {
    const newMode: NetworkMode = mode === 'full' ? 'text-only' : 'full';
    setMode(newMode);
  };

  const handleRefresh = async () => {
    await measureSpeed();
  };

  return (
    <div className={`network-mode-indicator ${className}`}>
      <div className="flex items-center gap-2">
        <span className={`text-2xl ${getQualityColor(quality)}`}>
          {getQualityIcon(quality)}
        </span>
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${getQualityColor(quality)}`}>
              {getModeLabel(mode)}
            </span>
            
            {isTextOnlyMode && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                Low Bandwidth
              </span>
            )}
          </div>
          
          {showDetails && (
            <div className="text-sm text-gray-600 mt-1">
              <div>{getModeDescription(mode)}</div>
              <div className="flex gap-4 mt-1">
                <span>Speed: {Math.round(averageSpeedKbps)} kbps</span>
                <span>Latency: {Math.round(latencyMs)} ms</span>
                <span className="capitalize">Quality: {quality}</span>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            title="Refresh network speed"
          >
            🔄
          </button>
          
          {allowManualOverride && (
            <button
              onClick={handleToggleMode}
              className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded"
              title="Toggle network mode"
            >
              {mode === 'full' ? '📶 → 📝' : '📝 → 📶'}
            </button>
          )}
        </div>
      </div>

      {isTextOnlyMode && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
          <strong>Text-Only Mode Active:</strong> Network speed is below 100 kbps. 
          Audio features are disabled to improve performance.
        </div>
      )}
    </div>
  );
};

export default NetworkModeIndicator;
