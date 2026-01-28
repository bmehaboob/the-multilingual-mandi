/**
 * Offline Notification Hook
 * 
 * Provides voice notifications when network status changes
 * Requirements: 12.4
 */

import { useEffect, useRef } from 'react';
import { useOnlineStatus } from './useServiceWorker';
import { AudioFeedbackSystem } from './audio/AudioFeedbackSystem';

export interface OfflineNotificationConfig {
  enabled: boolean;
  language: string;
  volume?: number;
}

/**
 * Hook that provides voice notifications for network status changes
 * Requirement 12.4: Provide voice notification when going offline/online
 * 
 * @param config - Configuration for offline notifications
 */
export function useOfflineNotification(config: OfflineNotificationConfig): void {
  const isOnline = useOnlineStatus();
  const audioFeedbackRef = useRef<AudioFeedbackSystem | null>(null);
  const previousOnlineStatusRef = useRef<boolean | null>(null);
  const isInitializedRef = useRef<boolean>(false);

  // Initialize audio feedback system
  useEffect(() => {
    if (!config.enabled) {
      return;
    }

    const initAudioFeedback = async () => {
      try {
        const audioFeedback = new AudioFeedbackSystem({
          language: config.language,
          enabled: true,
          volume: config.volume || 0.7,
          useTTS: true,
        });

        await audioFeedback.initialize();
        audioFeedbackRef.current = audioFeedback;
        isInitializedRef.current = true;
      } catch (error) {
        console.error('Failed to initialize audio feedback for offline notifications:', error);
      }
    };

    initAudioFeedback();

    return () => {
      if (audioFeedbackRef.current) {
        audioFeedbackRef.current.cleanup();
        audioFeedbackRef.current = null;
        isInitializedRef.current = false;
      }
    };
  }, [config.enabled]);

  // Monitor online status changes and provide voice notifications
  useEffect(() => {
    // Skip on first render (don't announce initial state)
    if (previousOnlineStatusRef.current === null) {
      previousOnlineStatusRef.current = isOnline;
      return;
    }

    // Only announce if status actually changed
    if (previousOnlineStatusRef.current === isOnline) {
      return;
    }

    // Update previous status
    previousOnlineStatusRef.current = isOnline;

    // Provide voice notification if enabled and initialized
    if (config.enabled && isInitializedRef.current && audioFeedbackRef.current) {
      if (isOnline) {
        // Going online
        audioFeedbackRef.current.playStateFeedback('online');
      } else {
        // Going offline
        audioFeedbackRef.current.playStateFeedback('offline');
      }
    }
  }, [isOnline, config.enabled]);

  // Update language when it changes
  useEffect(() => {
    if (audioFeedbackRef.current && isInitializedRef.current) {
      audioFeedbackRef.current.setLanguage(config.language);
    }
  }, [config.language]);

  // Update volume when it changes
  useEffect(() => {
    if (audioFeedbackRef.current && isInitializedRef.current && config.volume !== undefined) {
      audioFeedbackRef.current.setVolume(config.volume);
    }
  }, [config.volume]);
}

/**
 * Hook that returns both online status and provides voice notifications
 * 
 * @param config - Configuration for offline notifications
 * @returns Current online status
 */
export function useOfflineNotificationWithStatus(
  config: OfflineNotificationConfig
): boolean {
  const isOnline = useOnlineStatus();
  useOfflineNotification(config);
  return isOnline;
}
