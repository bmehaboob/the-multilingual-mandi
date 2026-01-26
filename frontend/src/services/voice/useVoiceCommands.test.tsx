/**
 * Unit tests for useVoiceCommands hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVoiceCommands, UseVoiceCommandsOptions } from './useVoiceCommands';

describe('useVoiceCommands', () => {
  let defaultOptions: UseVoiceCommandsOptions;

  beforeEach(() => {
    defaultOptions = {
      language: 'en',
      confirmationRequired: true,
      onCommandExecuted: vi.fn(),
      onError: vi.fn(),
    };
  });

  it('should initialize with no pending command', () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    expect(result.current.pendingCommand).toBeNull();
    expect(result.current.isWaitingForConfirmation).toBe(false);
    expect(result.current.confirmationMessage).toBeNull();
  });

  it('should recognize command and set pending state', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
      expect(result.current.pendingCommand?.action).toBe('navigate_home');
      expect(result.current.isWaitingForConfirmation).toBe(true);
      expect(result.current.confirmationMessage).not.toBeNull();
    });
  });

  it('should execute command on confirmation', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    // Recognize command
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
    });

    // Confirm command
    await act(async () => {
      await result.current.confirmPendingCommand();
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).toBeNull();
      expect(result.current.isWaitingForConfirmation).toBe(false);
      expect(defaultOptions.onCommandExecuted).toHaveBeenCalled();
    });
  });

  it('should cancel pending command', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    // Recognize command
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
    });

    // Cancel command
    act(() => {
      result.current.cancelPendingCommand();
    });

    expect(result.current.pendingCommand).toBeNull();
    expect(result.current.isWaitingForConfirmation).toBe(false);
  });

  it('should handle voice confirmation (yes)', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    // Recognize command
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
    });

    // Confirm with voice
    await act(async () => {
      await result.current.processVoiceInput('yes', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).toBeNull();
      expect(defaultOptions.onCommandExecuted).toHaveBeenCalled();
    });
  });

  it('should handle voice cancellation (no)', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    // Recognize command
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
    });

    // Cancel with voice
    await act(async () => {
      await result.current.processVoiceInput('no', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).toBeNull();
      expect(defaultOptions.onCommandExecuted).not.toHaveBeenCalled();
    });
  });

  it('should execute immediately when confirmation not required', async () => {
    const options = { ...defaultOptions, confirmationRequired: false };
    const { result } = renderHook(() => useVoiceCommands(options));
    
    await act(async () => {
      await result.current.processVoiceInput('go home', 'en');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).toBeNull();
      expect(options.onCommandExecuted).toHaveBeenCalled();
    });
  });

  it('should update language', () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    act(() => {
      result.current.setLanguage('hi');
    });

    // Language should be updated (no error thrown)
    expect(() => result.current.setLanguage('hi')).not.toThrow();
  });

  it('should update confirmation requirement', () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    act(() => {
      result.current.setConfirmationRequired(false);
    });

    // Should not throw
    expect(() => result.current.setConfirmationRequired(false)).not.toThrow();
  });

  it('should handle errors', async () => {
    const { result } = renderHook(() => useVoiceCommands(defaultOptions));
    
    // Process unrecognized command (should not throw)
    await act(async () => {
      await result.current.processVoiceInput('random text', 'en');
    });

    expect(result.current.pendingCommand).toBeNull();
  });

  it('should recognize Hindi commands', async () => {
    const options = { ...defaultOptions, language: 'hi' };
    const { result } = renderHook(() => useVoiceCommands(options));
    
    await act(async () => {
      await result.current.processVoiceInput('कीमत जांचो', 'hi');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
      expect(result.current.pendingCommand?.action).toBe('check_price');
      expect(result.current.confirmationMessage).toContain('कीमत');
    });
  });

  it('should recognize Telugu commands', async () => {
    const options = { ...defaultOptions, language: 'te' };
    const { result } = renderHook(() => useVoiceCommands(options));
    
    await act(async () => {
      await result.current.processVoiceInput('సంభాషణలు', 'te');
    });

    await waitFor(() => {
      expect(result.current.pendingCommand).not.toBeNull();
      expect(result.current.pendingCommand?.action).toBe('navigate_conversations');
    });
  });
});
