/**
 * React Hook for Audio Feedback System
 * 
 * Provides easy access to audio feedback functionality in React components
 */

import { useEffect, useRef, useState } from 'react';
import { AudioFeedbackSystem, AudioFeedbackConfig, SystemState, ActionPrompt } from './AudioFeedbackSystem';

export interface UseAudioFeedbackOptions {
  language?: string;
  enabled?: boolean;
  volume?: number;
  useTTS?: boolean;
}

export interface UseAudioFeedbackReturn {
  playStateFeedback: (state: SystemState, customMessage?: string) => Promise<void>;
  playActionPrompt: (action: ActionPrompt, customMessage?: string) => Promise<void>;
  playCustomMessage: (message: string) => Promise<void>;
  setLanguage: (language: string) => void;
  setEnabled: (enabled: boolean) => void;
  setVolume: (volume: number) => void;
  stop: () => void;
  clearQueue: () => void;
  isPlaying: boolean;
  isInitialized: boolean;
}

/**
 * Hook to use the audio feedback system
 */
export function useAudioFeedback(options: UseAudioFeedbackOptions = {}): UseAudioFeedbackReturn {
  const {
    language = 'en',
    enabled = true,
    volume = 0.7,
    useTTS = true,
  } = options;

  const feedbackSystemRef = useRef<AudioFeedbackSystem | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  // Initialize the audio feedback system
  useEffect(() => {
    const config: AudioFeedbackConfig = {
      language,
      enabled,
      volume,
      useTTS,
    };

    const feedbackSystem = new AudioFeedbackSystem(config);
    feedbackSystemRef.current = feedbackSystem;

    feedbackSystem.initialize()
      .then(() => {
        setIsInitialized(true);
      })
      .catch((error) => {
        console.error('Failed to initialize audio feedback:', error);
      });

    return () => {
      feedbackSystem.cleanup();
    };
  }, []);

  // Update language when it changes
  useEffect(() => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setLanguage(language);
    }
  }, [language]);

  // Update enabled state when it changes
  useEffect(() => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setEnabled(enabled);
    }
  }, [enabled]);

  // Update volume when it changes
  useEffect(() => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setVolume(volume);
    }
  }, [volume]);

  const playStateFeedback = async (state: SystemState, customMessage?: string): Promise<void> => {
    if (!feedbackSystemRef.current || !isInitialized) {
      return;
    }

    setIsPlaying(true);
    try {
      await feedbackSystemRef.current.playStateFeedback(state, customMessage);
    } finally {
      setIsPlaying(false);
    }
  };

  const playActionPrompt = async (action: ActionPrompt, customMessage?: string): Promise<void> => {
    if (!feedbackSystemRef.current || !isInitialized) {
      return;
    }

    setIsPlaying(true);
    try {
      await feedbackSystemRef.current.playActionPrompt(action, customMessage);
    } finally {
      setIsPlaying(false);
    }
  };

  const playCustomMessage = async (message: string): Promise<void> => {
    if (!feedbackSystemRef.current || !isInitialized) {
      return;
    }

    setIsPlaying(true);
    try {
      await feedbackSystemRef.current.playCustomMessage(message);
    } finally {
      setIsPlaying(false);
    }
  };

  const setLanguage = (newLanguage: string): void => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setLanguage(newLanguage);
    }
  };

  const setEnabled = (newEnabled: boolean): void => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setEnabled(newEnabled);
    }
  };

  const setVolume = (newVolume: number): void => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.setVolume(newVolume);
    }
  };

  const stop = (): void => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.stop();
      setIsPlaying(false);
    }
  };

  const clearQueue = (): void => {
    if (feedbackSystemRef.current) {
      feedbackSystemRef.current.clearQueue();
    }
  };

  return {
    playStateFeedback,
    playActionPrompt,
    playCustomMessage,
    setLanguage,
    setEnabled,
    setVolume,
    stop,
    clearQueue,
    isPlaying,
    isInitialized,
  };
}
