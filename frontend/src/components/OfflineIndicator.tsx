/**
 * Offline Indicator Component
 * 
 * Displays offline status and service worker update notifications
 * Requirements: 12.4, 19.1
 */

import React from 'react';
import { useServiceWorker } from '../services/useServiceWorker';

interface OfflineIndicatorProps {
  className?: string;
}

/**
 * Component that shows offline status and update notifications
 * Requirement 12.4: Notify users when operating in offline mode
 */
export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({ className = '' }) => {
  const [{ isOnline, isUpdateAvailable }, { updateServiceWorker }] = useServiceWorker();

  return (
    <div className={`offline-indicator ${className}`}>
      {/* Offline Status Banner */}
      {!isOnline && (
        <div
          className="offline-banner"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            backgroundColor: '#ff9800',
            color: '#fff',
            padding: '8px 16px',
            textAlign: 'center',
            zIndex: 9999,
            fontSize: '14px',
            fontWeight: 500,
          }}
          role="alert"
          aria-live="polite"
        >
          📡 You are currently offline. Some features may be limited.
        </div>
      )}

      {/* Update Available Banner */}
      {isUpdateAvailable && (
        <div
          className="update-banner"
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            backgroundColor: '#2196f3',
            color: '#fff',
            padding: '12px 16px',
            textAlign: 'center',
            zIndex: 9999,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '12px',
          }}
          role="alert"
          aria-live="polite"
        >
          <span>A new version is available!</span>
          <button
            onClick={updateServiceWorker}
            style={{
              backgroundColor: '#fff',
              color: '#2196f3',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '14px',
            }}
            aria-label="Update application to new version"
          >
            Update Now
          </button>
        </div>
      )}
    </div>
  );
};

export default OfflineIndicator;
