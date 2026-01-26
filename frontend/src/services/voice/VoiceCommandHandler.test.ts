/**
 * Unit tests for VoiceCommandHandler
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VoiceCommandHandler, VoiceCommandConfig, VoiceCommand } from './VoiceCommandHandler';

describe('VoiceCommandHandler', () => {
  let handler: VoiceCommandHandler;
  let mockConfig: VoiceCommandConfig;

  beforeEach(() => {
    mockConfig = {
      language: 'en',
      confirmationRequired: true,
      onCommandRecognized: vi.fn(),
      onCommandExecuted: vi.fn(),
      onCommandCancelled: vi.fn(),
    };
    handler = new VoiceCommandHandler(mockConfig);
  });

  describe('recognizeCommand', () => {
    it('should recognize English home navigation command', () => {
      const command = handler.recognizeCommand('go home', 'en');
      expect(command).not.toBeNull();
      expect(command?.action).toBe('navigate_home');
      expect(command?.language).toBe('en');
      expect(command?.confidence).toBeGreaterThan(0);
    });

    it('should recognize Hindi price check command', () => {
      const command = handler.recognizeCommand('कीमत जांचो', 'hi');
      expect(command).not.toBeNull();
      expect(command?.action).toBe('check_price');
      expect(command?.language).toBe('hi');
    });

    it('should recognize Telugu conversation command', () => {
      const command = handler.recognizeCommand('సంభాషణలు', 'te');
      expect(command).not.toBeNull();
      expect(command?.action).toBe('navigate_conversations');
      expect(command?.language).toBe('te');
    });

    it('should recognize Tamil history command', () => {
      const command = handler.recognizeCommand('வரலாறு', 'ta');
      expect(command).not.toBeNull();
      expect(command?.action).toBe('navigate_history');
      expect(command?.language).toBe('ta');
    });

    it('should return null for unrecognized command', () => {
      const command = handler.recognizeCommand('random text', 'en');
      expect(command).toBeNull();
    });

    it('should return null for unsupported language', () => {
      const command = handler.recognizeCommand('some text', 'unsupported');
      expect(command).toBeNull();
    });

    it('should handle case-insensitive matching', () => {
      const command = handler.recognizeCommand('GO HOME', 'en');
      expect(command).not.toBeNull();
      expect(command?.action).toBe('navigate_home');
    });
  });

  describe('getConfirmationMessage', () => {
    it('should return English confirmation message', () => {
      const command: VoiceCommand = {
        action: 'navigate_home',
        language: 'en',
        confidence: 1.0,
      };
      const message = handler.getConfirmationMessage(command);
      expect(message).toBe('Do you want to go home?');
    });

    it('should return Hindi confirmation message', () => {
      const command: VoiceCommand = {
        action: 'check_price',
        language: 'hi',
        confidence: 1.0,
      };
      const message = handler.getConfirmationMessage(command);
      expect(message).toBe('क्या आप कीमत जांचना चाहते हैं?');
    });

    it('should return Telugu confirmation message', () => {
      const command: VoiceCommand = {
        action: 'start_conversation',
        language: 'te',
        confidence: 1.0,
      };
      const message = handler.getConfirmationMessage(command);
      expect(message).toBe('మీరు కొత్త సంభాషణ ప్రారంభించాలనుకుంటున్నారా?');
    });

    it('should return default message for unsupported language', () => {
      const command: VoiceCommand = {
        action: 'navigate_home',
        language: 'unsupported',
        confidence: 1.0,
      };
      const message = handler.getConfirmationMessage(command);
      expect(message).toContain('navigate home');
    });
  });

  describe('processCommand', () => {
    it('should recognize and store pending command when confirmation required', async () => {
      const result = await handler.processCommand('go home', 'en');
      expect(result).toBe(true);
      expect(handler.getPendingCommand()).not.toBeNull();
      expect(handler.getPendingCommand()?.action).toBe('navigate_home');
      expect(mockConfig.onCommandRecognized).toHaveBeenCalled();
    });

    it('should execute immediately when confirmation not required', async () => {
      handler.setConfirmationRequired(false);
      const result = await handler.processCommand('go home', 'en');
      expect(result).toBe(true);
      expect(mockConfig.onCommandExecuted).toHaveBeenCalled();
    });

    it('should return false for unrecognized command', async () => {
      const result = await handler.processCommand('random text', 'en');
      expect(result).toBe(false);
    });
  });

  describe('confirmCommand', () => {
    it('should execute pending command on confirmation', async () => {
      await handler.processCommand('go home', 'en');
      expect(handler.getPendingCommand()).not.toBeNull();

      const result = await handler.confirmCommand();
      expect(result).toBe(true);
      expect(handler.getPendingCommand()).toBeNull();
      expect(mockConfig.onCommandExecuted).toHaveBeenCalled();
    });

    it('should return false when no pending command', async () => {
      const result = await handler.confirmCommand();
      expect(result).toBe(false);
    });
  });

  describe('cancelCommand', () => {
    it('should cancel pending command', async () => {
      await handler.processCommand('go home', 'en');
      expect(handler.getPendingCommand()).not.toBeNull();

      handler.cancelCommand();
      expect(handler.getPendingCommand()).toBeNull();
      expect(mockConfig.onCommandCancelled).toHaveBeenCalled();
    });

    it('should not throw when no pending command', () => {
      expect(() => handler.cancelCommand()).not.toThrow();
    });
  });

  describe('isConfirmation', () => {
    it('should recognize English yes confirmation', () => {
      expect(handler.isConfirmation('yes', 'en')).toBe('yes');
      expect(handler.isConfirmation('yeah', 'en')).toBe('yes');
      expect(handler.isConfirmation('ok', 'en')).toBe('yes');
    });

    it('should recognize English no confirmation', () => {
      expect(handler.isConfirmation('no', 'en')).toBe('no');
      expect(handler.isConfirmation('cancel', 'en')).toBe('no');
      expect(handler.isConfirmation('stop', 'en')).toBe('no');
    });

    it('should recognize Hindi yes confirmation', () => {
      expect(handler.isConfirmation('हां', 'hi')).toBe('yes');
      expect(handler.isConfirmation('जी हां', 'hi')).toBe('yes');
      expect(handler.isConfirmation('ठीक है', 'hi')).toBe('yes');
    });

    it('should recognize Hindi no confirmation', () => {
      expect(handler.isConfirmation('नहीं', 'hi')).toBe('no');
      expect(handler.isConfirmation('मत करो', 'hi')).toBe('no');
    });

    it('should recognize Telugu yes confirmation', () => {
      expect(handler.isConfirmation('అవును', 'te')).toBe('yes');
      expect(handler.isConfirmation('సరే', 'te')).toBe('yes');
    });

    it('should recognize Telugu no confirmation', () => {
      expect(handler.isConfirmation('కాదు', 'te')).toBe('no');
      expect(handler.isConfirmation('వద్దు', 'te')).toBe('no');
    });

    it('should return null for non-confirmation text', () => {
      expect(handler.isConfirmation('random text', 'en')).toBeNull();
    });
  });

  describe('setLanguage', () => {
    it('should update language', () => {
      handler.setLanguage('hi');
      const command = handler.recognizeCommand('होम पर जाओ', 'hi');
      expect(command).not.toBeNull();
    });
  });

  describe('setConfirmationRequired', () => {
    it('should update confirmation requirement', async () => {
      handler.setConfirmationRequired(false);
      await handler.processCommand('go home', 'en');
      expect(handler.getPendingCommand()).toBeNull();
      expect(mockConfig.onCommandExecuted).toHaveBeenCalled();
    });
  });

  describe('confidence calculation', () => {
    it('should calculate high confidence for exact match', () => {
      const command = handler.recognizeCommand('go home', 'en');
      expect(command?.confidence).toBeGreaterThanOrEqual(0.9);
    });

    it('should calculate lower confidence for partial match', () => {
      const command = handler.recognizeCommand('I want to go home please', 'en');
      expect(command?.confidence).toBeGreaterThan(0);
      expect(command?.confidence).toBeLessThanOrEqual(1.0);
    });
  });
});
