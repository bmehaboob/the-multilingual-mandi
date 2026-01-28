/**
 * Tests for NetworkSpeedDetector
 * Requirements: 10.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  NetworkSpeedDetector,
  NetworkSpeedResult,
  NETWORK_THRESHOLDS,
  getNetworkSpeedDetector,
  resetNetworkSpeedDetector,
} from './NetworkSpeedDetector';

describe('NetworkSpeedDetector', () => {
  let detector: NetworkSpeedDetector;

  beforeEach(() => {
    detector = new NetworkSpeedDetector({
      measurementInterval: 100, // Short interval for testing
      samplesForAverage: 3,
    });

    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    // Mock fetch
    global.fetch = vi.fn();
  });

  afterEach(() => {
    detector.destroy();
    vi.clearAllMocks();
  });

  describe('Speed Measurement', () => {
    it('should measure network speed', async () => {
      // Mock successful fetch
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      const result = await detector.measureSpeed();

      expect(result).toBeDefined();
      expect(result.speedKbps).toBeGreaterThanOrEqual(0);
      expect(result.latencyMs).toBeGreaterThanOrEqual(0);
      expect(result.timestamp).toBeGreaterThan(0);
    });

    it('should return offline result when not online', async () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const result = await detector.measureSpeed();

      expect(result.speedKbps).toBe(0);
      expect(result.latencyMs).toBe(Infinity);
      expect(result.connectionType).toBe('offline');
    });

    it('should handle measurement errors gracefully', async () => {
      // Mock fetch failure
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      const result = await detector.measureSpeed();

      // Should return a conservative estimate
      expect(result.speedKbps).toBeLessThan(100);
      expect(result.latencyMs).toBeGreaterThan(0);
    });

    it('should store measurement in history', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      await detector.measureSpeed();

      const history = detector.getSpeedHistory();
      expect(history.length).toBe(1);
    });
  });

  describe('Speed History', () => {
    it('should maintain speed history', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      await detector.measureSpeed();
      await detector.measureSpeed();
      await detector.measureSpeed();

      const history = detector.getSpeedHistory();
      expect(history.length).toBe(3);
    });

    it('should limit history size', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      // Add more samples than the limit
      for (let i = 0; i < 10; i++) {
        await detector.measureSpeed();
      }

      const history = detector.getSpeedHistory();
      expect(history.length).toBeLessThanOrEqual(6); // samplesForAverage * 2
    });

    it('should get latest speed measurement', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      await detector.measureSpeed();
      await detector.measureSpeed();

      const latest = detector.getLatestSpeed();
      expect(latest).toBeDefined();
      expect(latest!.timestamp).toBeGreaterThan(0);
    });

    it('should return null for latest speed when no measurements', () => {
      const latest = detector.getLatestSpeed();
      expect(latest).toBeNull();
    });

    it('should clear history', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      await detector.measureSpeed();
      expect(detector.getSpeedHistory().length).toBe(1);

      detector.clearHistory();
      expect(detector.getSpeedHistory().length).toBe(0);
    });
  });

  describe('Average Speed Calculation', () => {
    it('should calculate average speed from recent samples', async () => {
      // Mock measurements with known speeds
      const mockMeasurement = (speed: number): NetworkSpeedResult => ({
        speedKbps: speed,
        latencyMs: 100,
        timestamp: Date.now(),
      });

      // Manually add measurements
      detector['speedHistory'] = [
        mockMeasurement(100),
        mockMeasurement(200),
        mockMeasurement(300),
      ];

      const avgSpeed = detector.getAverageSpeed();
      expect(avgSpeed).toBe(200); // (100 + 200 + 300) / 3
    });

    it('should return 0 for average when no measurements', () => {
      const avgSpeed = detector.getAverageSpeed();
      expect(avgSpeed).toBe(0);
    });

    it('should use only recent samples for average', async () => {
      const mockMeasurement = (speed: number): NetworkSpeedResult => ({
        speedKbps: speed,
        latencyMs: 100,
        timestamp: Date.now(),
      });

      // Add 5 measurements, but only last 3 should be used
      detector['speedHistory'] = [
        mockMeasurement(100),
        mockMeasurement(100),
        mockMeasurement(200),
        mockMeasurement(300),
        mockMeasurement(400),
      ];

      const avgSpeed = detector.getAverageSpeed();
      expect(avgSpeed).toBe(300); // (200 + 300 + 400) / 3
    });
  });

  describe('Network Quality Classification', () => {
    it('should classify fast network (>= 1000 kbps)', () => {
      detector['speedHistory'] = [
        { speedKbps: 1500, latencyMs: 50, timestamp: Date.now() },
        { speedKbps: 1200, latencyMs: 50, timestamp: Date.now() },
        { speedKbps: 1000, latencyMs: 50, timestamp: Date.now() },
      ];

      const quality = detector.getNetworkQuality();
      expect(quality).toBe('fast');
    });

    it('should classify moderate network (>= 500 kbps)', () => {
      detector['speedHistory'] = [
        { speedKbps: 700, latencyMs: 100, timestamp: Date.now() },
        { speedKbps: 600, latencyMs: 100, timestamp: Date.now() },
        { speedKbps: 500, latencyMs: 100, timestamp: Date.now() },
      ];

      const quality = detector.getNetworkQuality();
      expect(quality).toBe('moderate');
    });

    it('should classify slow network (>= 100 kbps)', () => {
      detector['speedHistory'] = [
        { speedKbps: 150, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 120, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 100, latencyMs: 200, timestamp: Date.now() },
      ];

      const quality = detector.getNetworkQuality();
      expect(quality).toBe('slow');
    });

    it('should classify very slow network (< 100 kbps)', () => {
      detector['speedHistory'] = [
        { speedKbps: 80, latencyMs: 500, timestamp: Date.now() },
        { speedKbps: 60, latencyMs: 500, timestamp: Date.now() },
        { speedKbps: 50, latencyMs: 500, timestamp: Date.now() },
      ];

      const quality = detector.getNetworkQuality();
      expect(quality).toBe('very-slow');
    });

    it('should classify offline when not online', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const quality = detector.getNetworkQuality();
      expect(quality).toBe('offline');
    });
  });

  describe('Text-Only Mode Detection', () => {
    it('should recommend text-only mode when speed < 100 kbps', () => {
      // Requirement 10.3: Switch to text-only mode when speed < 100 kbps
      detector['speedHistory'] = [
        { speedKbps: 80, latencyMs: 500, timestamp: Date.now() },
        { speedKbps: 70, latencyMs: 500, timestamp: Date.now() },
        { speedKbps: 60, latencyMs: 500, timestamp: Date.now() },
      ];

      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      expect(shouldUseTextOnly).toBe(true);
    });

    it('should not recommend text-only mode when speed >= 100 kbps', () => {
      detector['speedHistory'] = [
        { speedKbps: 150, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 120, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 100, latencyMs: 200, timestamp: Date.now() },
      ];

      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      expect(shouldUseTextOnly).toBe(false);
    });

    it('should not recommend text-only mode when offline (speed = 0)', () => {
      detector['speedHistory'] = [
        { speedKbps: 0, latencyMs: Infinity, timestamp: Date.now() },
      ];

      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      expect(shouldUseTextOnly).toBe(false);
    });

    it('should handle edge case at exactly 100 kbps threshold', () => {
      detector['speedHistory'] = [
        { speedKbps: 100, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 100, latencyMs: 200, timestamp: Date.now() },
        { speedKbps: 100, latencyMs: 200, timestamp: Date.now() },
      ];

      const shouldUseTextOnly = detector.shouldUseTextOnlyMode();
      expect(shouldUseTextOnly).toBe(false); // >= 100 kbps, so full mode
    });
  });

  describe('Subscription and Listeners', () => {
    it('should notify listeners on new measurements', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      const listener = vi.fn();
      detector.subscribe(listener);

      await detector.measureSpeed();

      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener).toHaveBeenCalledWith(expect.objectContaining({
        speedKbps: expect.any(Number),
        latencyMs: expect.any(Number),
        timestamp: expect.any(Number),
      }));
    });

    it('should support multiple listeners', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      const listener1 = vi.fn();
      const listener2 = vi.fn();
      
      detector.subscribe(listener1);
      detector.subscribe(listener2);

      await detector.measureSpeed();

      expect(listener1).toHaveBeenCalledTimes(1);
      expect(listener2).toHaveBeenCalledTimes(1);
    });

    it('should unsubscribe listeners', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['test']),
      });

      const listener = vi.fn();
      const unsubscribe = detector.subscribe(listener);

      await detector.measureSpeed();
      expect(listener).toHaveBeenCalledTimes(1);

      unsubscribe();
      await detector.measureSpeed();
      expect(listener).toHaveBeenCalledTimes(1); // Not called again
    });
  });

  describe('Start and Stop', () => {
    it('should start monitoring', () => {
      detector.start();
      // Should not throw
    });

    it('should not start twice', () => {
      detector.start();
      detector.start(); // Should log but not throw
    });

    it('should stop monitoring', () => {
      detector.start();
      detector.stop();
      // Should not throw
    });

    it('should stop gracefully when not started', () => {
      detector.stop();
      // Should not throw
    });
  });

  describe('Singleton Instance', () => {
    afterEach(() => {
      resetNetworkSpeedDetector();
    });

    it('should return singleton instance', () => {
      const instance1 = getNetworkSpeedDetector();
      const instance2 = getNetworkSpeedDetector();

      expect(instance1).toBe(instance2);
    });

    it('should reset singleton instance', () => {
      const instance1 = getNetworkSpeedDetector();
      resetNetworkSpeedDetector();
      const instance2 = getNetworkSpeedDetector();

      expect(instance1).not.toBe(instance2);
    });
  });

  describe('Cleanup', () => {
    it('should clean up resources on destroy', () => {
      detector.start();
      
      const listener = vi.fn();
      detector.subscribe(listener);

      detector.destroy();

      expect(detector.getSpeedHistory().length).toBe(0);
    });
  });
});
