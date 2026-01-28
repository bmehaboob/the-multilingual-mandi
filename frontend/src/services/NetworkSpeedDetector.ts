/**
 * Network Speed Detector
 * 
 * Detects network connection speed and quality
 * Requirements: 10.3
 */

/**
 * Network speed measurement result
 */
export interface NetworkSpeedResult {
  speedKbps: number;
  latencyMs: number;
  timestamp: number;
  connectionType?: string;
}

/**
 * Network quality classification
 */
export type NetworkQuality = 'fast' | 'moderate' | 'slow' | 'very-slow' | 'offline';

/**
 * Network speed thresholds (in kbps)
 */
export const NETWORK_THRESHOLDS = {
  FAST: 1000, // >= 1 Mbps
  MODERATE: 500, // >= 500 kbps
  SLOW: 100, // >= 100 kbps (threshold for text-only mode)
  VERY_SLOW: 0, // < 100 kbps
} as const;

/**
 * Configuration for network speed detection
 */
export interface NetworkSpeedConfig {
  testUrl?: string;
  testFileSize?: number; // in bytes
  measurementInterval?: number; // in ms
  samplesForAverage?: number;
}

const DEFAULT_CONFIG: Required<NetworkSpeedConfig> = {
  testUrl: '/api/health', // Small endpoint for speed testing
  testFileSize: 1024, // 1 KB
  measurementInterval: 30000, // 30 seconds
  samplesForAverage: 3,
};

/**
 * NetworkSpeedDetector
 * 
 * Detects and monitors network connection speed
 * Requirement 10.3: Detect network speed and switch to text-only mode when < 100 kbps
 */
export class NetworkSpeedDetector {
  private config: Required<NetworkSpeedConfig>;
  private speedHistory: NetworkSpeedResult[] = [];
  private measurementTimer: number | null = null;
  private listeners: Set<(result: NetworkSpeedResult) => void> = new Set();
  private isRunning = false;

  constructor(config?: NetworkSpeedConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Start continuous network speed monitoring
   */
  start(): void {
    if (this.isRunning) {
      console.log('NetworkSpeedDetector already running');
      return;
    }

    this.isRunning = true;
    console.log('NetworkSpeedDetector started');

    // Perform initial measurement
    this.measureSpeed().catch(error => {
      console.error('Initial speed measurement failed:', error);
    });

    // Set up periodic measurements
    this.measurementTimer = window.setInterval(() => {
      this.measureSpeed().catch(error => {
        console.error('Periodic speed measurement failed:', error);
      });
    }, this.config.measurementInterval);
  }

  /**
   * Stop network speed monitoring
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;

    if (this.measurementTimer !== null) {
      clearInterval(this.measurementTimer);
      this.measurementTimer = null;
    }

    console.log('NetworkSpeedDetector stopped');
  }

  /**
   * Measure current network speed
   * Uses download timing to estimate bandwidth
   */
  async measureSpeed(): Promise<NetworkSpeedResult> {
    if (!navigator.onLine) {
      const offlineResult: NetworkSpeedResult = {
        speedKbps: 0,
        latencyMs: Infinity,
        timestamp: Date.now(),
        connectionType: 'offline',
      };
      this.addMeasurement(offlineResult);
      return offlineResult;
    }

    try {
      // Use Network Information API if available
      const connection = this.getConnectionInfo();

      // Measure latency with a simple ping
      const latencyMs = await this.measureLatency();

      // Estimate speed based on connection type or perform actual test
      let speedKbps: number;

      if (connection?.downlink) {
        // Use reported downlink speed (in Mbps, convert to kbps)
        speedKbps = connection.downlink * 1000;
      } else {
        // Perform actual download test
        speedKbps = await this.performDownloadTest();
      }

      const result: NetworkSpeedResult = {
        speedKbps,
        latencyMs,
        timestamp: Date.now(),
        connectionType: connection?.effectiveType || 'unknown',
      };

      this.addMeasurement(result);
      return result;
    } catch (error) {
      console.error('Speed measurement failed:', error);
      
      // Return a conservative estimate on error
      const fallbackResult: NetworkSpeedResult = {
        speedKbps: 50, // Assume very slow connection
        latencyMs: 1000,
        timestamp: Date.now(),
        connectionType: 'unknown',
      };
      
      this.addMeasurement(fallbackResult);
      return fallbackResult;
    }
  }

  /**
   * Measure network latency with a simple ping
   */
  private async measureLatency(): Promise<number> {
    const startTime = performance.now();
    
    try {
      await fetch(this.config.testUrl, {
        method: 'HEAD',
        cache: 'no-cache',
      });
      
      const endTime = performance.now();
      return endTime - startTime;
    } catch (error) {
      console.error('Latency measurement failed:', error);
      return 1000; // Default to 1 second on error
    }
  }

  /**
   * Perform actual download test to measure speed
   */
  private async performDownloadTest(): Promise<number> {
    const startTime = performance.now();
    
    try {
      // Add cache-busting parameter
      const testUrl = `${this.config.testUrl}?t=${Date.now()}`;
      
      const response = await fetch(testUrl, {
        cache: 'no-cache',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Read the response body
      await response.blob();
      
      const endTime = performance.now();
      const durationSeconds = (endTime - startTime) / 1000;
      
      // Calculate speed in kbps
      const fileSizeKb = this.config.testFileSize / 1024;
      const speedKbps = (fileSizeKb * 8) / durationSeconds;
      
      return speedKbps;
    } catch (error) {
      console.error('Download test failed:', error);
      return 50; // Default to very slow on error
    }
  }

  /**
   * Get connection information from Network Information API
   */
  private getConnectionInfo(): any {
    // @ts-ignore - Network Information API may not be in TypeScript definitions
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    return connection;
  }

  /**
   * Add a measurement to history
   */
  private addMeasurement(result: NetworkSpeedResult): void {
    this.speedHistory.push(result);

    // Keep only recent samples
    const maxSamples = this.config.samplesForAverage * 2;
    if (this.speedHistory.length > maxSamples) {
      this.speedHistory = this.speedHistory.slice(-maxSamples);
    }

    // Notify listeners
    this.listeners.forEach(listener => listener(result));
  }

  /**
   * Get the most recent speed measurement
   */
  getLatestSpeed(): NetworkSpeedResult | null {
    if (this.speedHistory.length === 0) {
      return null;
    }
    return this.speedHistory[this.speedHistory.length - 1];
  }

  /**
   * Get average speed from recent measurements
   */
  getAverageSpeed(): number {
    if (this.speedHistory.length === 0) {
      return 0;
    }

    const recentSamples = this.speedHistory.slice(-this.config.samplesForAverage);
    const sum = recentSamples.reduce((acc, result) => acc + result.speedKbps, 0);
    return sum / recentSamples.length;
  }

  /**
   * Get current network quality classification
   */
  getNetworkQuality(): NetworkQuality {
    if (!navigator.onLine) {
      return 'offline';
    }

    const avgSpeed = this.getAverageSpeed();

    if (avgSpeed >= NETWORK_THRESHOLDS.FAST) {
      return 'fast';
    } else if (avgSpeed >= NETWORK_THRESHOLDS.MODERATE) {
      return 'moderate';
    } else if (avgSpeed >= NETWORK_THRESHOLDS.SLOW) {
      return 'slow';
    } else {
      return 'very-slow';
    }
  }

  /**
   * Check if network speed is below threshold for text-only mode
   * Requirement 10.3: Switch to text-only mode when speed < 100 kbps
   */
  shouldUseTextOnlyMode(): boolean {
    const avgSpeed = this.getAverageSpeed();
    return avgSpeed < NETWORK_THRESHOLDS.SLOW && avgSpeed > 0;
  }

  /**
   * Subscribe to speed measurement updates
   */
  subscribe(listener: (result: NetworkSpeedResult) => void): () => void {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get all speed measurements
   */
  getSpeedHistory(): NetworkSpeedResult[] {
    return [...this.speedHistory];
  }

  /**
   * Clear speed history
   */
  clearHistory(): void {
    this.speedHistory = [];
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.stop();
    this.listeners.clear();
    this.speedHistory = [];
  }
}

// Singleton instance
let networkSpeedDetectorInstance: NetworkSpeedDetector | null = null;

/**
 * Get the singleton instance of NetworkSpeedDetector
 */
export function getNetworkSpeedDetector(config?: NetworkSpeedConfig): NetworkSpeedDetector {
  if (!networkSpeedDetectorInstance) {
    networkSpeedDetectorInstance = new NetworkSpeedDetector(config);
  }
  return networkSpeedDetectorInstance;
}

/**
 * Reset the singleton instance (useful for testing)
 */
export function resetNetworkSpeedDetector(): void {
  if (networkSpeedDetectorInstance) {
    networkSpeedDetectorInstance.destroy();
    networkSpeedDetectorInstance = null;
  }
}
