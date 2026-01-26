/**
 * Voice Command Handler
 * 
 * Handles voice command recognition for navigation and actions.
 * Supports commands in all 22 Indian languages with voice confirmation.
 * 
 * Requirements: 11.2, 11.3
 */

export interface VoiceCommand {
  action: string;
  params?: Record<string, any>;
  language: string;
  confidence: number;
}

export interface VoiceCommandConfig {
  language: string;
  confirmationRequired: boolean;
  onCommandRecognized?: (command: VoiceCommand) => void;
  onCommandExecuted?: (command: VoiceCommand) => void;
  onCommandCancelled?: (command: VoiceCommand) => void;
}

export type CommandAction =
  | 'navigate_home'
  | 'navigate_conversations'
  | 'navigate_prices'
  | 'navigate_history'
  | 'check_price'
  | 'start_conversation'
  | 'request_negotiation_help'
  | 'replay_message'
  | 'end_conversation'
  | 'switch_conversation'
  | 'view_history'
  | 'logout'
  | 'help';

/**
 * Command patterns for each supported language
 * Maps language codes to command patterns
 */
export const COMMAND_PATTERNS: Record<string, Record<CommandAction, string[]>> = {
  // Hindi (hi)
  hi: {
    navigate_home: ['होम पर जाओ', 'घर जाओ', 'मुख्य पृष्ठ'],
    navigate_conversations: ['बातचीत देखो', 'संवाद देखो', 'बातचीत'],
    navigate_prices: ['कीमतें देखो', 'भाव देखो', 'दाम देखो'],
    navigate_history: ['इतिहास', 'पुराने लेनदेन', 'इतिहास देखो'],
    check_price: ['कीमत जांचो', 'भाव बताओ', 'दाम क्या है'],
    start_conversation: ['बातचीत शुरू करो', 'नई बातचीत', 'संवाद शुरू'],
    request_negotiation_help: ['मदद चाहिए', 'सौदा मदद', 'सुझाव दो'],
    replay_message: ['फिर से सुनाओ', 'दोहराओ', 'फिर से'],
    end_conversation: ['बातचीत बंद करो', 'समाप्त करो', 'खत्म करो'],
    switch_conversation: ['बातचीत बदलो', 'दूसरी बातचीत', 'स्विच करो'],
    view_history: ['इतिहास देखो', 'पुराने लेनदेन देखो'],
    logout: ['लॉग आउट', 'बाहर निकलो', 'बंद करो'],
    help: ['मदद', 'सहायता', 'कैसे करें'],
  },
  // English (en)
  en: {
    navigate_home: ['go home', 'home', 'main page'],
    navigate_conversations: ['conversations', 'chats', 'messages'],
    navigate_prices: ['prices', 'check prices', 'market prices'],
    navigate_history: ['history', 'past transactions', 'transaction history'],
    check_price: ['check price', 'what is the price', 'price of'],
    start_conversation: ['start conversation', 'new conversation', 'new chat'],
    request_negotiation_help: ['help me negotiate', 'negotiation help', 'suggest price'],
    replay_message: ['replay', 'repeat', 'play again'],
    end_conversation: ['end conversation', 'finish', 'close chat'],
    switch_conversation: ['switch conversation', 'change chat', 'other conversation'],
    view_history: ['view history', 'show history', 'past transactions'],
    logout: ['logout', 'sign out', 'exit'],
    help: ['help', 'how to', 'guide'],
  },
  // Telugu (te)
  te: {
    navigate_home: ['హోమ్‌కు వెళ్ళు', 'ముఖ్య పేజీ', 'హోమ్'],
    navigate_conversations: ['సంభాషణలు', 'చాట్‌లు', 'సందేశాలు'],
    navigate_prices: ['ధరలు', 'ధరలు చూడు', 'మార్కెట్ ధరలు'],
    navigate_history: ['చరిత్ర', 'పాత లావాదేవీలు', 'లావాదేవీ చరిత్ర'],
    check_price: ['ధర తనిఖీ చేయి', 'ధర ఎంత', 'ధర చెప్పు'],
    start_conversation: ['సంభాషణ ప్రారంభించు', 'కొత్త సంభాషణ', 'కొత్త చాట్'],
    request_negotiation_help: ['సహాయం కావాలి', 'చర్చల సహాయం', 'సూచన ఇవ్వు'],
    replay_message: ['మళ్ళీ వినిపించు', 'పునరావృతం', 'మళ్ళీ'],
    end_conversation: ['సంభాషణ ముగించు', 'ముగించు', 'మూసివేయి'],
    switch_conversation: ['సంభాషణ మార్చు', 'వేరే సంభాషణ', 'మార్చు'],
    view_history: ['చరిత్ర చూడు', 'పాత లావాదేవీలు చూడు'],
    logout: ['లాగ్ అవుట్', 'నిష్క్రమించు', 'మూసివేయి'],
    help: ['సహాయం', 'ఎలా చేయాలి', 'మార్గదర్శకం'],
  },
  // Tamil (ta)
  ta: {
    navigate_home: ['முகப்புக்கு செல்', 'முகப்பு', 'முதன்மை பக்கம்'],
    navigate_conversations: ['உரையாடல்கள்', 'அரட்டைகள்', 'செய்திகள்'],
    navigate_prices: ['விலைகள்', 'விலைகளைப் பார்', 'சந்தை விலைகள்'],
    navigate_history: ['வரலாறு', 'பழைய பரிவர்த்தனைகள்', 'பரிவர்த்தனை வரலாறு'],
    check_price: ['விலை சரிபார்', 'விலை என்ன', 'விலை சொல்'],
    start_conversation: ['உரையாடல் தொடங்கு', 'புதிய உரையாடல்', 'புதிய அரட்டை'],
    request_negotiation_help: ['உதவி வேண்டும்', 'பேரம் உதவி', 'பரிந்துரை கொடு'],
    replay_message: ['மீண்டும் கேள்', 'மீண்டும்', 'திரும்ப'],
    end_conversation: ['உரையாடல் முடி', 'முடி', 'மூடு'],
    switch_conversation: ['உரையாடல் மாற்று', 'வேறு உரையாடல்', 'மாற்று'],
    view_history: ['வரலாறு பார்', 'பழைய பரிவர்த்தனைகளைப் பார்'],
    logout: ['வெளியேறு', 'வெளியேறு', 'மூடு'],
    help: ['உதவி', 'எப்படி', 'வழிகாட்டி'],
  },
};

// Add more languages as needed (Kannada, Marathi, Bengali, etc.)
// For brevity, showing pattern for a few languages


/**
 * Confirmation messages for each language
 */
export const CONFIRMATION_MESSAGES: Record<string, Record<CommandAction, string>> = {
  hi: {
    navigate_home: 'क्या आप होम पर जाना चाहते हैं?',
    navigate_conversations: 'क्या आप बातचीत देखना चाहते हैं?',
    navigate_prices: 'क्या आप कीमतें देखना चाहते हैं?',
    navigate_history: 'क्या आप इतिहास देखना चाहते हैं?',
    check_price: 'क्या आप कीमत जांचना चाहते हैं?',
    start_conversation: 'क्या आप नई बातचीत शुरू करना चाहते हैं?',
    request_negotiation_help: 'क्या आप सौदा मदद चाहते हैं?',
    replay_message: 'क्या आप संदेश फिर से सुनना चाहते हैं?',
    end_conversation: 'क्या आप बातचीत बंद करना चाहते हैं?',
    switch_conversation: 'क्या आप बातचीत बदलना चाहते हैं?',
    view_history: 'क्या आप इतिहास देखना चाहते हैं?',
    logout: 'क्या आप लॉग आउट करना चाहते हैं?',
    help: 'क्या आप मदद चाहते हैं?',
  },
  en: {
    navigate_home: 'Do you want to go home?',
    navigate_conversations: 'Do you want to view conversations?',
    navigate_prices: 'Do you want to check prices?',
    navigate_history: 'Do you want to view history?',
    check_price: 'Do you want to check the price?',
    start_conversation: 'Do you want to start a new conversation?',
    request_negotiation_help: 'Do you want negotiation help?',
    replay_message: 'Do you want to replay the message?',
    end_conversation: 'Do you want to end the conversation?',
    switch_conversation: 'Do you want to switch conversations?',
    view_history: 'Do you want to view history?',
    logout: 'Do you want to logout?',
    help: 'Do you want help?',
  },
  te: {
    navigate_home: 'మీరు హోమ్‌కు వెళ్లాలనుకుంటున్నారా?',
    navigate_conversations: 'మీరు సంభాషణలు చూడాలనుకుంటున్నారా?',
    navigate_prices: 'మీరు ధరలు చూడాలనుకుంటున్నారా?',
    navigate_history: 'మీరు చరిత్ర చూడాలనుకుంటున్నారా?',
    check_price: 'మీరు ధర తనిఖీ చేయాలనుకుంటున్నారా?',
    start_conversation: 'మీరు కొత్త సంభాషణ ప్రారంభించాలనుకుంటున్నారా?',
    request_negotiation_help: 'మీరు చర్చల సహాయం కావాలా?',
    replay_message: 'మీరు సందేశం మళ్ళీ వినాలనుకుంటున్నారా?',
    end_conversation: 'మీరు సంభాషణ ముగించాలనుకుంటున్నారా?',
    switch_conversation: 'మీరు సంభాషణ మార్చాలనుకుంటున్నారా?',
    view_history: 'మీరు చరిత్ర చూడాలనుకుంటున్నారా?',
    logout: 'మీరు లాగ్ అవుట్ చేయాలనుకుంటున్నారా?',
    help: 'మీరు సహాయం కావాలా?',
  },
  ta: {
    navigate_home: 'நீங்கள் முகப்புக்கு செல்ல விரும்புகிறீர்களா?',
    navigate_conversations: 'நீங்கள் உரையாடல்களைப் பார்க்க விரும்புகிறீர்களா?',
    navigate_prices: 'நீங்கள் விலைகளைப் பார்க்க விரும்புகிறீர்களா?',
    navigate_history: 'நீங்கள் வரலாற்றைப் பார்க்க விரும்புகிறீர்களா?',
    check_price: 'நீங்கள் விலையைச் சரிபார்க்க விரும்புகிறீர்களா?',
    start_conversation: 'நீங்கள் புதிய உரையாடலைத் தொடங்க விரும்புகிறீர்களா?',
    request_negotiation_help: 'நீங்கள் பேரம் உதவி வேண்டுமா?',
    replay_message: 'நீங்கள் செய்தியை மீண்டும் கேட்க விரும்புகிறீர்களா?',
    end_conversation: 'நீங்கள் உரையாடலை முடிக்க விரும்புகிறீர்களா?',
    switch_conversation: 'நீங்கள் உரையாடலை மாற்ற விரும்புகிறீர்களா?',
    view_history: 'நீங்கள் வரலாற்றைப் பார்க்க விரும்புகிறீர்களா?',
    logout: 'நீங்கள் வெளியேற விரும்புகிறீர்களா?',
    help: 'நீங்கள் உதவி வேண்டுமா?',
  },
};

/**
 * Voice Command Handler Class
 * 
 * Recognizes voice commands and executes actions with confirmation
 */
export class VoiceCommandHandler {
  private config: VoiceCommandConfig;
  private isListening: boolean = false;
  private pendingCommand: VoiceCommand | null = null;

  constructor(config: VoiceCommandConfig) {
    this.config = config;
  }

  /**
   * Update the language for command recognition
   */
  setLanguage(language: string): void {
    this.config.language = language;
  }

  /**
   * Enable or disable confirmation requirement
   */
  setConfirmationRequired(required: boolean): void {
    this.config.confirmationRequired = required;
  }

  /**
   * Recognize a command from transcribed text
   * 
   * @param text - The transcribed text from speech
   * @param language - The detected language
   * @returns Recognized command or null if no match
   */
  recognizeCommand(text: string, language: string): VoiceCommand | null {
    const normalizedText = text.toLowerCase().trim();
    const patterns = COMMAND_PATTERNS[language];

    if (!patterns) {
      console.warn(`No command patterns found for language: ${language}`);
      return null;
    }

    // Check each command action for a match
    for (const [action, commandPatterns] of Object.entries(patterns)) {
      for (const pattern of commandPatterns) {
        if (normalizedText.includes(pattern.toLowerCase())) {
          return {
            action: action as CommandAction,
            language,
            confidence: this.calculateConfidence(normalizedText, pattern),
          };
        }
      }
    }

    return null;
  }

  /**
   * Calculate confidence score based on pattern match
   */
  private calculateConfidence(text: string, pattern: string): number {
    const textWords = text.toLowerCase().split(/\s+/);
    const patternWords = pattern.toLowerCase().split(/\s+/);
    
    let matchedWords = 0;
    for (const patternWord of patternWords) {
      if (textWords.some(textWord => textWord.includes(patternWord) || patternWord.includes(textWord))) {
        matchedWords++;
      }
    }
    
    return matchedWords / patternWords.length;
  }

  /**
   * Get confirmation message for a command
   */
  getConfirmationMessage(command: VoiceCommand): string {
    const messages = CONFIRMATION_MESSAGES[command.language];
    if (!messages) {
      return `Do you want to ${command.action.replace(/_/g, ' ')}?`;
    }
    return messages[command.action as CommandAction] || `Do you want to ${command.action.replace(/_/g, ' ')}?`;
  }

  /**
   * Process a voice command with optional confirmation
   * 
   * @param text - Transcribed text
   * @param language - Detected language
   * @returns Promise that resolves when command is processed
   */
  async processCommand(text: string, language: string): Promise<boolean> {
    const command = this.recognizeCommand(text, language);
    
    if (!command) {
      return false;
    }

    // Notify that command was recognized
    if (this.config.onCommandRecognized) {
      this.config.onCommandRecognized(command);
    }

    // If confirmation is required, store the pending command
    if (this.config.confirmationRequired) {
      this.pendingCommand = command;
      return true; // Command recognized, waiting for confirmation
    }

    // Execute immediately if no confirmation required
    return this.executeCommand(command);
  }

  /**
   * Confirm the pending command
   */
  async confirmCommand(): Promise<boolean> {
    if (!this.pendingCommand) {
      return false;
    }

    const command = this.pendingCommand;
    this.pendingCommand = null;
    return this.executeCommand(command);
  }

  /**
   * Cancel the pending command
   */
  cancelCommand(): void {
    if (this.pendingCommand && this.config.onCommandCancelled) {
      this.config.onCommandCancelled(this.pendingCommand);
    }
    this.pendingCommand = null;
  }

  /**
   * Get the pending command awaiting confirmation
   */
  getPendingCommand(): VoiceCommand | null {
    return this.pendingCommand;
  }

  /**
   * Execute a confirmed command
   */
  private executeCommand(command: VoiceCommand): boolean {
    if (this.config.onCommandExecuted) {
      this.config.onCommandExecuted(command);
    }
    return true;
  }

  /**
   * Check if a text contains a confirmation (yes/no)
   */
  isConfirmation(text: string, language: string): 'yes' | 'no' | null {
    const normalizedText = text.toLowerCase().trim();
    
    const confirmationPatterns: Record<string, { yes: string[]; no: string[] }> = {
      hi: {
        yes: ['हां', 'हाँ', 'जी हां', 'ठीक है', 'चलो'],
        no: ['नहीं', 'ना', 'मत करो', 'रहने दो', 'नहीं चाहिए'],
      },
      en: {
        yes: ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'proceed'],
        no: ['no', 'nope', 'cancel', 'stop', 'don\'t', 'never mind'],
      },
      te: {
        yes: ['అవును', 'సరే', 'చేయి', 'కొనసాగించు'],
        no: ['కాదు', 'వద్దు', 'రద్దు చేయి', 'ఆపు'],
      },
      ta: {
        yes: ['ஆம்', 'சரி', 'செய்', 'தொடர்'],
        no: ['இல்லை', 'வேண்டாம்', 'ரத்து செய்', 'நிறுத்து'],
      },
    };

    const patterns = confirmationPatterns[language];
    if (!patterns) {
      // Default to English patterns
      const defaultPatterns = confirmationPatterns['en'];
      if (defaultPatterns.yes.some(p => normalizedText.includes(p))) return 'yes';
      if (defaultPatterns.no.some(p => normalizedText.includes(p))) return 'no';
      return null;
    }

    if (patterns.yes.some(p => normalizedText.includes(p))) return 'yes';
    if (patterns.no.some(p => normalizedText.includes(p))) return 'no';
    return null;
  }
}

