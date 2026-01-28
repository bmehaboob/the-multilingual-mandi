/**
 * Network Mode Demo Component
 * 
 * Demonstrates adaptive network mode switching functionality
 * Requirements: 10.3
 */

import React, { useState } from 'react';
import { NetworkModeIndicator } from './NetworkModeIndicator';
import { useNetworkSpeed } from '../services/useNetworkSpeed';

/**
 * NetworkModeDemo Component
 * 
 * Interactive demo showing how the platform adapts to network conditions
 * Requirement 10.3: Switch to text-only mode when speed < 100 kbps
 */
export const NetworkModeDemo: React.FC = () => {
  const {
    speedKbps,
    averageSpeedKbps,
    latencyMs,
    quality,
    mode,
    isTextOnlyMode,
    measureSpeed,
  } = useNetworkSpeed();

  const [simulatedSpeed, setSimulatedSpeed] = useState<number | null>(null);

  const simulateNetworkSpeed = (speed: number) => {
    setSimulatedSpeed(speed);
    // In a real implementation, this would inject the simulated speed
    // into the detector for testing purposes
  };

  const getFeatureStatus = (feature: string): 'enabled' | 'disabled' => {
    if (isTextOnlyMode) {
      // In text-only mode, audio features are disabled
      if (feature === 'voice-input' || feature === 'voice-output' || feature === 'audio-playback') {
        return 'disabled';
      }
    }
    return 'enabled';
  };

  const features = [
    { id: 'text-input', name: 'Text Input', alwaysEnabled: true },
    { id: 'text-output', name: 'Text Output', alwaysEnabled: true },
    { id: 'voice-input', name: 'Voice Input', alwaysEnabled: false },
    { id: 'voice-output', name: 'Voice Output', alwaysEnabled: false },
    { id: 'audio-playback', name: 'Audio Playback', alwaysEnabled: false },
    { id: 'translation', name: 'Translation', alwaysEnabled: true },
    { id: 'price-check', name: 'Price Check', alwaysEnabled: true },
  ];

  return (
    <div className="network-mode-demo p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Adaptive Network Mode Demo</h1>
      
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded">
        <h2 className="text-xl font-semibold mb-2">About Adaptive Mode</h2>
        <p className="text-gray-700">
          The platform automatically detects network speed and switches to text-only mode 
          when bandwidth is below 100 kbps. This ensures the platform remains usable even 
          on slow 2G/3G connections by disabling audio features that consume bandwidth.
        </p>
      </div>

      {/* Network Status */}
      <div className="mb-6 p-4 bg-white border border-gray-200 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Current Network Status</h2>
        <NetworkModeIndicator showDetails={true} allowManualOverride={true} />
      </div>

      {/* Network Simulation */}
      <div className="mb-6 p-4 bg-white border border-gray-200 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Simulate Network Conditions</h2>
        <p className="text-sm text-gray-600 mb-4">
          Click a button to simulate different network speeds and see how the platform adapts:
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => simulateNetworkSpeed(2000)}
            className="px-4 py-3 bg-green-100 hover:bg-green-200 rounded border border-green-300"
          >
            <div className="font-semibold">4G/LTE</div>
            <div className="text-sm">~2000 kbps</div>
          </button>
          
          <button
            onClick={() => simulateNetworkSpeed(500)}
            className="px-4 py-3 bg-blue-100 hover:bg-blue-200 rounded border border-blue-300"
          >
            <div className="font-semibold">3G</div>
            <div className="text-sm">~500 kbps</div>
          </button>
          
          <button
            onClick={() => simulateNetworkSpeed(150)}
            className="px-4 py-3 bg-yellow-100 hover:bg-yellow-200 rounded border border-yellow-300"
          >
            <div className="font-semibold">Slow 3G</div>
            <div className="text-sm">~150 kbps</div>
          </button>
          
          <button
            onClick={() => simulateNetworkSpeed(50)}
            className="px-4 py-3 bg-orange-100 hover:bg-orange-200 rounded border border-orange-300"
          >
            <div className="font-semibold">2G</div>
            <div className="text-sm">~50 kbps</div>
          </button>
        </div>

        {simulatedSpeed !== null && (
          <div className="mt-4 p-3 bg-gray-50 rounded">
            <p className="text-sm">
              <strong>Simulated Speed:</strong> {simulatedSpeed} kbps
              {simulatedSpeed < 100 && (
                <span className="ml-2 text-orange-600">
                  (Below 100 kbps threshold - Text-Only Mode would activate)
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Feature Availability */}
      <div className="mb-6 p-4 bg-white border border-gray-200 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Feature Availability</h2>
        <p className="text-sm text-gray-600 mb-4">
          Current mode: <strong className={isTextOnlyMode ? 'text-orange-600' : 'text-green-600'}>
            {mode === 'text-only' ? 'Text-Only Mode' : 'Full Mode'}
          </strong>
        </p>
        
        <div className="space-y-2">
          {features.map(feature => {
            const status = feature.alwaysEnabled ? 'enabled' : getFeatureStatus(feature.id);
            const isEnabled = status === 'enabled';
            
            return (
              <div
                key={feature.id}
                className={`flex items-center justify-between p-3 rounded ${
                  isEnabled ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
                }`}
              >
                <span className="font-medium">{feature.name}</span>
                <span className={`px-3 py-1 rounded text-sm ${
                  isEnabled 
                    ? 'bg-green-200 text-green-800' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {isEnabled ? '✓ Enabled' : '✗ Disabled'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="mb-6 p-4 bg-white border border-gray-200 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Current Speed</div>
            <div className="text-2xl font-bold">{Math.round(speedKbps)} kbps</div>
          </div>
          
          <div className="p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Average Speed</div>
            <div className="text-2xl font-bold">{Math.round(averageSpeedKbps)} kbps</div>
          </div>
          
          <div className="p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Latency</div>
            <div className="text-2xl font-bold">{Math.round(latencyMs)} ms</div>
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={measureSpeed}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            Measure Network Speed Now
          </button>
        </div>
      </div>

      {/* Bandwidth Savings */}
      {isTextOnlyMode && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <h2 className="text-xl font-semibold mb-2">Bandwidth Savings</h2>
          <p className="text-gray-700">
            Text-only mode is currently active, saving approximately 60-80% of bandwidth 
            by disabling audio features. This allows you to continue using the platform 
            for text-based communication, price checks, and negotiation assistance even 
            on very slow connections.
          </p>
        </div>
      )}

      {/* Technical Details */}
      <div className="p-4 bg-gray-50 border border-gray-200 rounded">
        <h2 className="text-xl font-semibold mb-2">Technical Details</h2>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          <li>Network speed is measured every 30 seconds</li>
          <li>Average speed is calculated from the last 3 measurements</li>
          <li>Text-only mode activates when average speed drops below 100 kbps</li>
          <li>Full mode resumes when average speed rises above 100 kbps</li>
          <li>Users can manually override the automatic mode switching</li>
          <li>Audio compression reduces bandwidth usage by 60%+ in full mode</li>
        </ul>
      </div>
    </div>
  );
};

export default NetworkModeDemo;
