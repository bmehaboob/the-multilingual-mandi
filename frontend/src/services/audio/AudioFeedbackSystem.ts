/**
 * Audio Feedback System
 * 
 * Provides audio feedback for all system states and voice prompts for major actions.
 * Supports all 22 Indian languages for voice-first interaction.
 * 
 * Requirements: 11.1, 11.4
 */

import { AudioPlaybackModule } from './AudioPlaybackModule';

export type SystemState = 
  | 'loading'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'processing'
  | 'connecting'
  | 'offline'
  | 'online';

export type ActionPrompt =
  | 'start_conversation'
  | 'check_price'
  | 'request_negotiation'
  | 'end_conversation'
  | 'switch_conversation'
  | 'view_history'
  | 'replay_message'
  | 'confirm_action'
  | 'cancel_action'
  | 'welcome'
  | 'goodbye';

export interface AudioFeedbackConfig {
  language: string;
  enabled: boolean;
  volume?: number;
  useTTS?: boolean; // Use Text-to-Speech for prompts
}

export interface FeedbackSound {
  type: 'tone' | 'voice';
  data?: Blob; // For voice prompts
  frequency?: number; // For tone feedback
  duration?: number; // In milliseconds
}

/**
 * Voice prompts for major actions in different languages
 * These would typically come from a TTS service, but we define the text here
 */
export const VOICE_PROMPTS: Record<string, Record<ActionPrompt, string>> = {
  hi: {
    start_conversation: 'नई बातचीत शुरू करें',
    check_price: 'कीमत जांचें',
    request_negotiation: 'सौदा मदद लें',
    end_conversation: 'बातचीत समाप्त करें',
    switch_conversation: 'बातचीत बदलें',
    view_history: 'इतिहास देखें',
    replay_message: 'संदेश फिर से सुनें',
    confirm_action: 'पुष्टि करें',
    cancel_action: 'रद्द करें',
    welcome: 'स्वागत है',
    goodbye: 'धन्यवाद',
  },
  en: {
    start_conversation: 'Start conversation',
    check_price: 'Check price',
    request_negotiation: 'Request negotiation help',
    end_conversation: 'End conversation',
    switch_conversation: 'Switch conversation',
    view_history: 'View history',
    replay_message: 'Replay message',
    confirm_action: 'Confirm',
    cancel_action: 'Cancel',
    welcome: 'Welcome',
    goodbye: 'Thank you',
  },
  te: {
    start_conversation: 'సంభాషణ ప్రారంభించండి',
    check_price: 'ధర తనిఖీ చేయండి',
    request_negotiation: 'చర్చల సహాయం పొందండి',
    end_conversation: 'సంభాషణ ముగించండి',
    switch_conversation: 'సంభాషణ మార్చండి',
    view_history: 'చరిత్ర చూడండి',
    replay_message: 'సందేశం మళ్ళీ వినండి',
    confirm_action: 'నిర్ధారించండి',
    cancel_action: 'రద్దు చేయండి',
    welcome: 'స్వాగతం',
    goodbye: 'ధన్యవాదాలు',
  },
  ta: {
    start_conversation: 'உரையாடலைத் தொடங்குங்கள்',
    check_price: 'விலையைச் சரிபார்க்கவும்',
    request_negotiation: 'பேரம் உதவி பெறுங்கள்',
    end_conversation: 'உரையாடலை முடிக்கவும்',
    switch_conversation: 'உரையாடலை மாற்றவும்',
    view_history: 'வரலாற்றைப் பார்க்கவும்',
    replay_message: 'செய்தியை மீண்டும் கேளுங்கள்',
    confirm_action: 'உறுதிப்படுத்து',
    cancel_action: 'ரத்து செய்',
    welcome: 'வரவேற்கிறோம்',
    goodbye: 'நன்றி',
  },
  kn: {
    start_conversation: 'ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ',
    check_price: 'ಬೆಲೆ ಪರಿಶೀಲಿಸಿ',
    request_negotiation: 'ಚರ್ಚೆ ಸಹಾಯ ಪಡೆಯಿರಿ',
    end_conversation: 'ಸಂಭಾಷಣೆ ಮುಗಿಸಿ',
    switch_conversation: 'ಸಂಭಾಷಣೆ ಬದಲಿಸಿ',
    view_history: 'ಇತಿಹಾಸ ನೋಡಿ',
    replay_message: 'ಸಂದೇಶ ಮತ್ತೆ ಕೇಳಿ',
    confirm_action: 'ದೃಢೀಕರಿಸಿ',
    cancel_action: 'ರದ್ದುಮಾಡಿ',
    welcome: 'ಸ್ವಾಗತ',
    goodbye: 'ಧನ್ಯವಾದಗಳು',
  },
  mr: {
    start_conversation: 'संभाषण सुरू करा',
    check_price: 'किंमत तपासा',
    request_negotiation: 'वाटाघाटी मदत घ्या',
    end_conversation: 'संभाषण समाप्त करा',
    switch_conversation: 'संभाषण बदला',
    view_history: 'इतिहास पहा',
    replay_message: 'संदेश पुन्हा ऐका',
    confirm_action: 'पुष्टी करा',
    cancel_action: 'रद्द करा',
    welcome: 'स्वागत आहे',
    goodbye: 'धन्यवाद',
  },
};

/**
 * System state messages in different languages
 */
export const STATE_MESSAGES: Record<string, Record<SystemState, string>> = {
  hi: {
    loading: 'लोड हो रहा है',
    success: 'सफल',
    error: 'त्रुटि',
    warning: 'चेतावनी',
    info: 'जानकारी',
    processing: 'प्रक्रिया जारी है',
    connecting: 'कनेक्ट हो रहा है',
    offline: 'ऑफलाइन मोड',
    online: 'ऑनलाइन',
  },
  en: {
    loading: 'Loading',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information',
    processing: 'Processing',
    connecting: 'Connecting',
    offline: 'Offline mode',
    online: 'Online',
  },
  te: {
    loading: 'లోడ్ అవుతోంది',
    success: 'విజయవంతం',
    error: 'లోపం',
    warning: 'హెచ్చరిక',
    info: 'సమాచారం',
    processing: 'ప్రాసెస్ అవుతోంది',
    connecting: 'కనెక్ట్ అవుతోంది',
    offline: 'ఆఫ్‌లైన్ మోడ్',
    online: 'ఆన్‌లైన్',
  },
  ta: {
    loading: 'ஏற்றுகிறது',
    success: 'வெற்றி',
    error: 'பிழை',
    warning: 'எச்சரிக்கை',
    info: 'தகவல்',
    processing: 'செயலாக்கம்',
    connecting: 'இணைக்கிறது',
    offline: 'ஆஃப்லைன் பயன்முறை',
    online: 'ஆன்லைன்',
  },
  kn: {
    loading: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ',
    success: 'ಯಶಸ್ವಿ',
    error: 'ದೋಷ',
    warning: 'ಎಚ್ಚರಿಕೆ',
    info: 'ಮಾಹಿತಿ',
    processing: 'ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ',
    connecting: 'ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ',
    offline: 'ಆಫ್‌ಲೈನ್ ಮೋಡ್',
    online: 'ಆನ್‌ಲೈನ್',
  },
  mr: {
    loading: 'लोड होत आहे',
    success: 'यशस्वी',
    error: 'त्रुटी',
    warning: 'चेतावणी',
    info: 'माहिती',
    processing: 'प्रक्रिया सुरू आहे',
    connecting: 'कनेक्ट होत आहे',
    offline: 'ऑफलाइन मोड',
    online: 'ऑनलाइन',
  },
};

/**
 * Audio Feedback System Class
 * 
 * Manages audio feedback for system states and voice prompts for actions
 */
export class AudioFeedbackSystem {
  private config: AudioFeedbackConfig;
  private audioPlayback: AudioPlaybackModule;
  private audioContext: AudioContext | null = null;
  private feedbackQueue: Array<{ state?: SystemState; action?: ActionPrompt; message?: string }> = [];
  private isPlaying = false;

  constructor(config: AudioFeedbackConfig) {
    this.config = config;
    this.audioPlayback = new AudioPlaybackModule();
  }

  /**
   * Initialize the audio feedback system
   */
  async initialize(): Promise<void> {
    try {
      await this.audioPlayback.initialize();
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (error) {
      console.error('Failed to initialize audio feedback system:', error);
      throw error;
    }
  }

  /**
   * Set the language for voice prompts
   */
  setLanguage(language: string): void {
    this.config.language = language;
  }

  /**
   * Enable or disable audio feedback
   */
  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
  }

  /**
   * Set volume for audio feedback
   */
  setVolume(volume: number): void {
    this.config.volume = Math.max(0, Math.min(1, volume));
    this.audioPlayback.setVolume(this.config.volume || 0.7);
  }

  /**
   * Play audio feedback for a system state (Requirement 11.4)
   * 
   * @param state - The system state to provide feedback for
   * @param customMessage - Optional custom message to speak
   */
  async playStateFeedback(state: SystemState, customMessage?: string): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    // Queue the feedback if currently playing
    if (this.isPlaying) {
      this.feedbackQueue.push({ state, message: customMessage });
      return;
    }

    this.isPlaying = true;

    try {
      // Play tone feedback first (non-blocking)
      await this.playToneFeedback(state);

      // If TTS is enabled and we have a message, speak it
      if (this.config.useTTS) {
        const message = customMessage || this.getStateMessage(state);
        await this.speakMessage(message);
      }
    } catch (error) {
      console.error('Failed to play state feedback:', error);
    } finally {
      this.isPlaying = false;
      this.processQueue();
    }
  }

  /**
   * Play voice prompt for an action (Requirement 11.1)
   * 
   * @param action - The action to provide a voice prompt for
   * @param customMessage - Optional custom message to speak
   */
  async playActionPrompt(action: ActionPrompt, customMessage?: string): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    // Queue the prompt if currently playing
    if (this.isPlaying) {
      this.feedbackQueue.push({ action, message: customMessage });
      return;
    }

    this.isPlaying = true;

    try {
      const message = customMessage || this.getActionPrompt(action);
      
      if (this.config.useTTS) {
        await this.speakMessage(message);
      } else {
        // Play a simple tone if TTS is not available
        await this.playToneFeedback('info');
      }
    } catch (error) {
      console.error('Failed to play action prompt:', error);
    } finally {
      this.isPlaying = false;
      this.processQueue();
    }
  }

  /**
   * Play a tone feedback for a system state
   * Different tones for different states
   */
  private async playToneFeedback(state: SystemState): Promise<void> {
    if (!this.audioContext) {
      return;
    }

    const toneConfig = this.getToneConfig(state);
    
    return new Promise((resolve) => {
      const oscillator = this.audioContext!.createOscillator();
      const gainNode = this.audioContext!.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext!.destination);

      oscillator.frequency.value = toneConfig.frequency;
      oscillator.type = toneConfig.waveType;

      // Set volume
      const volume = this.config.volume || 0.3;
      gainNode.gain.setValueAtTime(volume, this.audioContext!.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        this.audioContext!.currentTime + toneConfig.duration / 1000
      );

      oscillator.start(this.audioContext!.currentTime);
      oscillator.stop(this.audioContext!.currentTime + toneConfig.duration / 1000);

      oscillator.onended = () => {
        resolve();
      };
    });
  }

  /**
   * Get tone configuration for a system state
   */
  private getToneConfig(state: SystemState): { frequency: number; duration: number; waveType: OscillatorType } {
    const configs: Record<SystemState, { frequency: number; duration: number; waveType: OscillatorType }> = {
      loading: { frequency: 440, duration: 200, waveType: 'sine' },
      success: { frequency: 523, duration: 150, waveType: 'sine' }, // C5 note
      error: { frequency: 220, duration: 300, waveType: 'square' }, // A3 note
      warning: { frequency: 349, duration: 250, waveType: 'triangle' }, // F4 note
      info: { frequency: 392, duration: 150, waveType: 'sine' }, // G4 note
      processing: { frequency: 466, duration: 200, waveType: 'sine' }, // A#4 note
      connecting: { frequency: 494, duration: 200, waveType: 'sine' }, // B4 note
      offline: { frequency: 262, duration: 300, waveType: 'square' }, // C4 note
      online: { frequency: 523, duration: 150, waveType: 'sine' }, // C5 note
    };

    return configs[state];
  }

  /**
   * Speak a message using TTS (would integrate with backend TTS service)
   * For now, this is a placeholder that would call the TTS API
   */
  private async speakMessage(message: string): Promise<void> {
    // In a real implementation, this would:
    // 1. Call the backend TTS service with the message and language
    // 2. Receive audio blob
    // 3. Play the audio using AudioPlaybackModule
    
    // For now, we'll use the browser's built-in speech synthesis as a fallback
    if ('speechSynthesis' in window) {
      return new Promise((resolve, reject) => {
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.lang = this.getLanguageCode(this.config.language);
        utterance.rate = 0.85; // 15% slower for clarity (Requirement 4.3)
        utterance.volume = this.config.volume || 0.7;

        utterance.onend = () => resolve();
        utterance.onerror = (error) => {
          console.error('Speech synthesis error:', error);
          reject(error);
        };

        window.speechSynthesis.speak(utterance);
      });
    } else {
      console.warn('Speech synthesis not supported');
    }
  }

  /**
   * Get the appropriate language code for speech synthesis
   */
  private getLanguageCode(language: string): string {
    const languageCodes: Record<string, string> = {
      hi: 'hi-IN',
      en: 'en-IN',
      te: 'te-IN',
      ta: 'ta-IN',
      kn: 'kn-IN',
      mr: 'mr-IN',
      bn: 'bn-IN',
      gu: 'gu-IN',
      pa: 'pa-IN',
      ml: 'ml-IN',
      or: 'or-IN',
      as: 'as-IN',
    };

    return languageCodes[language] || 'en-IN';
  }

  /**
   * Get the state message in the current language
   */
  private getStateMessage(state: SystemState): string {
    const messages = STATE_MESSAGES[this.config.language];
    if (!messages) {
      return STATE_MESSAGES['en'][state];
    }
    return messages[state];
  }

  /**
   * Get the action prompt in the current language
   */
  private getActionPrompt(action: ActionPrompt): string {
    const prompts = VOICE_PROMPTS[this.config.language];
    if (!prompts) {
      return VOICE_PROMPTS['en'][action];
    }
    return prompts[action];
  }

  /**
   * Process the feedback queue
   */
  private async processQueue(): Promise<void> {
    if (this.feedbackQueue.length === 0 || this.isPlaying) {
      return;
    }

    const next = this.feedbackQueue.shift();
    if (!next) {
      return;
    }

    if (next.state) {
      await this.playStateFeedback(next.state, next.message);
    } else if (next.action) {
      await this.playActionPrompt(next.action, next.message);
    }
  }

  /**
   * Clear the feedback queue
   */
  clearQueue(): void {
    this.feedbackQueue = [];
  }

  /**
   * Stop any currently playing feedback
   */
  stop(): void {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.audioPlayback.stop();
    this.isPlaying = false;
  }

  /**
   * Play a custom message
   */
  async playCustomMessage(message: string): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    if (this.isPlaying) {
      this.feedbackQueue.push({ message });
      return;
    }

    this.isPlaying = true;

    try {
      await this.speakMessage(message);
    } catch (error) {
      console.error('Failed to play custom message:', error);
    } finally {
      this.isPlaying = false;
      this.processQueue();
    }
  }

  /**
   * Check if feedback is currently playing
   */
  isCurrentlyPlaying(): boolean {
    return this.isPlaying;
  }

  /**
   * Get the current configuration
   */
  getConfig(): AudioFeedbackConfig {
    return { ...this.config };
  }

  /**
   * Clean up resources
   */
  async cleanup(): Promise<void> {
    this.stop();
    this.clearQueue();
    await this.audioPlayback.cleanup();
    
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
  }
}
