/**
 * Unit Tests for OfflineIndicator Component
 * 
 * Tests offline status display, update notifications, and voice notifications
 * Requirement 12.4: Notify users when operating in offline mode
 * Requirement 12.4: Provide voice notification when going offline/online
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { OfflineIndicator } from './OfflineIndicator';
import * as useServiceWorkerModule from '../services/useServiceWorker';
import { useOfflineNotification } from '../services/useOfflineNotification';

// Mock the useServiceWorker hook
vi.mock('../services/useServiceWorker');

// Mock the useOfflineNotification hook
vi.mock('../services/useOfflineNotification', () => ({
  useOfflineNotification: vi.fn(),
}));

describe('OfflineIndicator Component', () => {
  const mockUpdateServiceWorker = vi.fn();
  const mockRefreshCacheStats = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not display offline banner when online', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const offlineBanner = screen.queryByText(/You are currently offline/i);
    expect(offlineBanner).toBeNull();
  });

  it('should display offline banner when offline', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: false,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const offlineBanner = screen.getByText(/You are currently offline/i);
    expect(offlineBanner).toBeTruthy();
  });

  it('should display offline banner with correct styling', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: false,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const offlineBanner = screen.getByText(/You are currently offline/i);
    expect(offlineBanner.style.backgroundColor).toBe('rgb(255, 152, 0)');
    expect(offlineBanner.style.color).toBe('rgb(255, 255, 255)');
  });

  it('should not display update banner when no update is available', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const updateBanner = screen.queryByText(/A new version is available/i);
    expect(updateBanner).toBeNull();
  });

  it('should display update banner when update is available', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: true,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const updateBanner = screen.getByText(/A new version is available/i);
    expect(updateBanner).toBeTruthy();
  });

  it('should call updateServiceWorker when update button is clicked', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: true,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const updateButton = screen.getByRole('button', { name: /Update application/i });
    fireEvent.click(updateButton);

    expect(mockUpdateServiceWorker).toHaveBeenCalledTimes(1);
  });

  it('should have proper accessibility attributes for offline banner', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: false,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const offlineBanner = screen.getByRole('alert');
    expect(offlineBanner.getAttribute('aria-live')).toBe('polite');
  });

  it('should have proper accessibility attributes for update banner', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: true,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const updateBanner = screen.getByText(/A new version is available/i).parentElement;
    expect(updateBanner?.getAttribute('role')).toBe('alert');
    expect(updateBanner?.getAttribute('aria-live')).toBe('polite');
  });

  it('should accept custom className prop', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: true,
        isUpdateAvailable: false,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    const { container } = render(<OfflineIndicator className="custom-class" />);
    const indicator = container.querySelector('.offline-indicator');
    
    expect(indicator?.className).toContain('custom-class');
  });

  it('should display both offline and update banners simultaneously', () => {
    vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
      {
        isOnline: false,
        isUpdateAvailable: true,
        isInstalled: false,
        cacheStats: null,
      },
      {
        updateServiceWorker: mockUpdateServiceWorker,
        refreshCacheStats: mockRefreshCacheStats,
      },
    ]);

    render(<OfflineIndicator />);

    const offlineBanner = screen.getByText(/You are currently offline/i);
    const updateBanner = screen.getByText(/A new version is available/i);

    expect(offlineBanner).toBeTruthy();
    expect(updateBanner).toBeTruthy();
  });

  describe('Voice Notifications', () => {
    it('should enable voice notifications by default', () => {
      vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
        {
          isOnline: true,
          isUpdateAvailable: false,
          isInstalled: false,
          cacheStats: null,
        },
        {
          updateServiceWorker: mockUpdateServiceWorker,
          refreshCacheStats: mockRefreshCacheStats,
        },
      ]);

      render(<OfflineIndicator />);

      // Voice notifications should be enabled by default
      expect(useOfflineNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: true,
        })
      );
    });

    it('should pass language prop to voice notifications', () => {
      vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
        {
          isOnline: true,
          isUpdateAvailable: false,
          isInstalled: false,
          cacheStats: null,
        },
        {
          updateServiceWorker: mockUpdateServiceWorker,
          refreshCacheStats: mockRefreshCacheStats,
        },
      ]);

      render(<OfflineIndicator language="hi" />);

      expect(useOfflineNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          language: 'hi',
        })
      );
    });

    it('should pass volume prop to voice notifications', () => {
      vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
        {
          isOnline: true,
          isUpdateAvailable: false,
          isInstalled: false,
          cacheStats: null,
        },
        {
          updateServiceWorker: mockUpdateServiceWorker,
          refreshCacheStats: mockRefreshCacheStats,
        },
      ]);

      render(<OfflineIndicator volume={0.9} />);

      expect(useOfflineNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          volume: 0.9,
        })
      );
    });

    it('should allow disabling voice notifications', () => {
      vi.spyOn(useServiceWorkerModule, 'useServiceWorker').mockReturnValue([
        {
          isOnline: true,
          isUpdateAvailable: false,
          isInstalled: false,
          cacheStats: null,
        },
        {
          updateServiceWorker: mockUpdateServiceWorker,
          refreshCacheStats: mockRefreshCacheStats,
        },
      ]);

      render(<OfflineIndicator enableVoiceNotifications={false} />);

      expect(useOfflineNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: false,
        })
      );
    });
  });
});
