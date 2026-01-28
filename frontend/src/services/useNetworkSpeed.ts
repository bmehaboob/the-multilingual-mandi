/**
 * Network Speed Hook
 * 
 * React hook for monitoring network speed and adaptive mode switching
 * Requirements: 10.3
 */

import { useState, useEffect, useCallback } from 'react';
import {
  NetworkSpeedDetector,
  NetworkSpeedResult,
  NetworkQuality,
  NetworkSpeedConfig,
  getNetworkSpeedDetector,
} from './NetworkSpeedDetector';

/**
 * Network mode based on connection speed
 */
export type NetworkMode = 'full' | 'text-only';

/**
 * Hook return value
 */
export interface UseNetworkSpeedResult {
  /** Current network speed in kbps */
  speedKbps: number;
  /** Average network speed in kbps */
  averageSpeedKbps: number;
  /** Network latency in ms */
  latencyMs: number;
  /** Network quality classification */
  quality: NetworkQuality;
  /** Current network mode (full or text-only) */
  mode: NetworkMode;
  /** Whether text-only mode is active */
  isTextOnlyMode: boolean;
  /** Latest speed measurement */
  latestMeasurement: NetworkSpeedResult | null;
  /** Manually trigger a speed measurement */
  measureSpeed: () => Promise<void>;
  /** Force a specific network mode */
  setMode: (mode: NetworkMode) => void;
}

/**
 * Hook for monitoring network speed and adaptive mode switching
 * 
 * Requirement 10.3: Detect network speed and switch to text-only mode when < 100 kbps
 * 
 * @param config - Optional configuration for network speed detection
 * @param autoStart - Whether to automatically start monitoring (default: true)
 * @returns Network speed information and mode
 */
export function useNetworkSpeed(
  config?: NetworkSpeedConfig,
  autoStart: boolean = true
): UseNetworkSpeedResult {
  const [detector] = useState<NetworkSpeedDetector>(() => getNetworkSpeedDetector(config));
  const [latestMeasurement, setLatestMeasurement] = useState<NetworkSpeedResult | null>(null);
  const [averageSpeed, setAverageSpeed] = useState<number>(0);
  const [quality, setQuality] = useState<NetworkQuality>('moderate');
  const [autoMode, setAutoMode] = useState<NetworkMode>('full');
  const [manualMode, setManualMode] = useState<NetworkMode | null>(null);

  // Update state when new measurements arrive
  useEffect(() => {
    const unsubscribe = detector.subscribe((result: NetworkSpeedResult) => {
      setLatestMeasurement(result);
      setAverageSpeed(detector.getAverageSpeed());
      setQuality(detector.getNetworkQuality());
      
      // Update auto mode based on speed
      // Requirement 10.3: Switch to text-only mode when speed < 100 kbps
      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      setAutoMode(shouldUseTextOnly ? 'text-only' : 'full');
    });

    return unsubscribe;
  }, [detector]);

  // Start/stop monitoring
  useEffect(() => {
    if (autoStart) {
      detector.start();
    }

    return () => {
      if (autoStart) {
        detector.stop();
      }
    };
  }, [detector, autoStart]);

  // Manually trigger a speed measurement
  const measureSpeed = useCallback(async () => {
    try {
      const result = await detector.measureSpeed();
      setLatestMeasurement(result);
      setAverageSpeed(detector.getAverageSpeed());
      setQuality(detector.getNetworkQuality());
      
      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      setAutoMode(shouldUseTextOnly ? 'text-only' : 'full');
    } catch (error) {
      console.error('Failed to measure network speed:', error);
    }
  }, [detector]);

  // Force a specific network mode
  const setMode = useCallback((mode: NetworkMode) => {
    setManualMode(mode);
  }, []);

  // Determine effective mode (manual override takes precedence)
  const effectiveMode = manualMode !== null ? manualMode : autoMode;

  return {
    speedKbps: latestMeasurement?.speedKbps || 0,
    averageSpeedKbps: averageSpeed,
    latencyMs: latestMeasurement?.latencyMs || 0,
    quality,
    mode: effectiveMode,
    isTextOnlyMode: effectiveMode === 'text-only',
    latestMeasurement,
    measureSpeed,
    setMode,
  };
}

/**
 * Hook that only returns whether text-only mode should be active
 * Simpler version for components that only need the mode
 * 
 * @param config - Optional configuration for network speed detection
 * @returns Whether text-only mode is active
 */
export function useTextOnlyMode(config?: NetworkSpeedConfig): boolean {
  const { isTextOnlyMode } = useNetworkSpeed(config);
  return isTextOnlyMode;
}

/**
 * Hook that returns network quality classification
 * 
 * @param config - Optional configuration for network speed detection
 * @returns Current network quality
 */
export function useNetworkQuality(config?: NetworkSpeedConfig): NetworkQuality {
  const { quality } = useNetworkSpeed(config);
  return quality;
}
