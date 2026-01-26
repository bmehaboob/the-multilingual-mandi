/**
 * React Hook for Voice Commands
 * 
 * Provides voice command functionality with confirmation flow
 * Requirements: 11.2, 11.3
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { VoiceCommandHandler, VoiceCommand, VoiceCommandConfig, CommandAction } from './VoiceCommandHandler';

export interface UseVoiceCommandsOptions {
  language: string;
  confirmationRequired?: boolean;
  onCommandExecuted?: (command: VoiceCommand) => void;
  onError?: (error: Error) => void;
}

export interface UseVoiceCommandsReturn {
  processVoiceInput: (text: string, language: string) => Promise<void>;
  confirmPendingCommand: () => Promise<void>;
  cancelPendingCommand: () => void;
  pendingCommand: VoiceCommand | null;
  isWaitingForConfirmation: boolean;
  confirmationMessage: string | null;
  setLanguage: (language: string) => void;
  setConfirmationRequired: (required: boolean) => void;
}

/**
 * Hook for managing voice commands
 */
export function useVoiceCommands(options: UseVoiceCommandsOptions): UseVoiceCommandsReturn {
  const [pendingCommand, setPendingCommand] = useState<VoiceCommand | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(null);
  const handlerRef = useRef<VoiceCommandHandler | null>(null);

  // Initialize handler
  useEffect(() => {
    const config: VoiceCommandConfig = {
      language: options.language,
      confirmationRequired: options.confirmationRequired ?? true,
      onCommandRecognized: (command) => {
        setPendingCommand(command);
        const message = handlerRef.current?.getConfirmationMessage(command) || null;
        setConfirmationMessage(message);
      },
      onCommandExecuted: (command) => {
        setPendingCommand(null);
        setConfirmationMessage(null);
        if (options.onCommandExecuted) {
          options.onCommandExecuted(command);
        }
      },
      onCommandCancelled: () => {
        setPendingCommand(null);
        setConfirmationMessage(null);
      },
    };

    handlerRef.current = new VoiceCommandHandler(config);
  }, [options.language, options.confirmationRequired, options.onCommandExecuted]);

  /**
   * Process voice input and recognize commands
   */
  const processVoiceInput = useCallback(async (text: string, language: string) => {
    if (!handlerRef.current) return;

    try {
      // If we're waiting for confirmation, check if this is a yes/no response
      if (pendingCommand) {
        const confirmation = handlerRef.current.isConfirmation(text, language);
        if (confirmation === 'yes') {
          await handlerRef.current.confirmCommand();
          return;
        } else if (confirmation === 'no') {
          handlerRef.current.cancelCommand();
          return;
        }
      }

      // Otherwise, try to recognize a new command
      await handlerRef.current.processCommand(text, language);
    } catch (error) {
      if (options.onError) {
        options.onError(error as Error);
      }
    }
  }, [pendingCommand, options]);

  /**
   * Confirm the pending command
   */
  const confirmPendingCommand = useCallback(async () => {
    if (!handlerRef.current) return;
    await handlerRef.current.confirmCommand();
  }, []);

  /**
   * Cancel the pending command
   */
  const cancelPendingCommand = useCallback(() => {
    if (!handlerRef.current) return;
    handlerRef.current.cancelCommand();
  }, []);

  /**
   * Update the language
   */
  const setLanguage = useCallback((language: string) => {
    if (!handlerRef.current) return;
    handlerRef.current.setLanguage(language);
  }, []);

  /**
   * Update confirmation requirement
   */
  const setConfirmationRequired = useCallback((required: boolean) => {
    if (!handlerRef.current) return;
    handlerRef.current.setConfirmationRequired(required);
  }, []);

  return {
    processVoiceInput,
    confirmPendingCommand,
    cancelPendingCommand,
    pendingCommand,
    isWaitingForConfirmation: pendingCommand !== null,
    confirmationMessage,
    setLanguage,
    setConfirmationRequired,
  };
}
