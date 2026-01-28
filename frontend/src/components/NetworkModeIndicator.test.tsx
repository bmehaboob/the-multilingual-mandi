/**
 * Tests for NetworkModeIndicator component
 * Requirements: 10.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NetworkModeIndicator } from './NetworkModeIndicator';
import { resetNetworkSpeedDetector } from '../services/NetworkSpeedDetector';

// Mock the useNetworkSpeed hook
vi.mock('../services/useNetworkSpeed', () => {
  const mockFn = vi.fn(() => ({
    speedKbps: 500,
    averageSpeedKbps: 500,
    latencyMs: 100,
    quality: 'moderate' as const,
    mode: 'full' as const,
    isTextOnlyMode: false,
    measureSpeed: vi.fn(),
    setMode: vi.fn(),
  }));
  
  return {
    useNetworkSpeed: mockFn,
  };
});

describe('NetworkModeIndicator', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });
  });

  afterEach(() => {
    resetNetworkSpeedDetector();
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render network mode indicator', () => {
      render(<NetworkModeIndicator />);
      
      const element = screen.getByText('Full Mode');
      expect(element).toBeTruthy();
    });

    it('should display network quality icon', () => {
      render(<NetworkModeIndicator />);
      
      // Should have an icon (emoji)
      const indicator = screen.getByText(/📶|📵/);
      expect(indicator).toBeTruthy();
    });

    it('should show refresh button', () => {
      render(<NetworkModeIndicator />);
      
      const refreshButton = screen.getByTitle('Refresh network speed');
      expect(refreshButton).toBeTruthy();
    });
  });

  describe('Detailed Information', () => {
    it('should show details when showDetails is true', () => {
      render(<NetworkModeIndicator showDetails={true} />);
      
      expect(screen.getByText(/Speed:/)).toBeTruthy();
      expect(screen.getByText(/Latency:/)).toBeTruthy();
      expect(screen.getByText(/Quality:/)).toBeTruthy();
    });

    it('should hide details when showDetails is false', () => {
      render(<NetworkModeIndicator showDetails={false} />);
      
      expect(screen.queryByText(/Speed:/)).toBeNull();
      expect(screen.queryByText(/Latency:/)).toBeNull();
    });
  });

  describe('Manual Override', () => {
    it('should show toggle button when allowManualOverride is true', () => {
      render(<NetworkModeIndicator allowManualOverride={true} />);
      
      const toggleButton = screen.getByTitle('Toggle network mode');
      expect(toggleButton).toBeTruthy();
    });

    it('should hide toggle button when allowManualOverride is false', () => {
      render(<NetworkModeIndicator allowManualOverride={false} />);
      
      const toggleButton = screen.queryByTitle('Toggle network mode');
      expect(toggleButton).toBeNull();
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      const { container } = render(<NetworkModeIndicator className="custom-class" />);
      
      const indicator = container.querySelector('.custom-class');
      expect(indicator).toBeTruthy();
    });
  });
});
