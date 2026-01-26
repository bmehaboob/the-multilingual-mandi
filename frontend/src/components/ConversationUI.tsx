/**
 * Conversation UI Component
 * 
 * Voice-first conversation interface with visual indicators for processing states.
 * Supports conversation switching with voice announcements.
 * 
 * Requirements: 5.2, 16.2, 16.4
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useVoiceCommands } from '../services/voice/useVoiceCommands';
import { useAudioFeedback } from '../services/audio/useAudioFeedback';

// Types
export interface Conversation {
  id: string;
  participants: string[];
  commodity?: string;
  status: 'active' | 'completed' | 'abandoned';
  created_at: string;
  updated_at?: string;
  message_count: number;
  last_message_at?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  original_text: string;
  original_language: string;
  translated_text: Record<string, string>;
  audio_url?: string;
  timestamp: string;
  message_metadata: Record<string, any>;
}

export type ProcessingState = 
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'translating'
  | 'synthesizing'
  | 'sending'
  | 'error';

export interface ConversationUIProps {
  userId: string;
  language: string;
  onSendMessage?: (conversationId: string, text: string, language: string) => Promise<void>;
  onSwitchConversation?: (conversationId: string) => void;
  onEndConversation?: (conversationId: string) => void;
}

/**
 * Processing state messages in different languages
 */
const PROCESSING_MESSAGES: Record<string, Record<ProcessingState, string>> = {
  hi: {
    idle: 'तैयार',
    listening: 'सुन रहा है...',
    transcribing: 'लिख रहा है...',
    translating: 'अनुवाद कर रहा है...',
    synthesizing: 'आवाज़ बना रहा है...',
    sending: 'भेज रहा है...',
    error: 'त्रुटि',
  },
  en: {
    idle: 'Ready',
    listening: 'Listening...',
    transcribing: 'Transcribing...',
    translating: 'Translating...',
    synthesizing: 'Synthesizing...',
    sending: 'Sending...',
    error: 'Error',
  },
  te: {
    idle: 'సిద్ధంగా ఉంది',
    listening: 'వింటోంది...',
    transcribing: 'రాస్తోంది...',
    translating: 'అనువదిస్తోంది...',
    synthesizing: 'స్వరం సృష్టిస్తోంది...',
    sending: 'పంపుతోంది...',
    error: 'లోపం',
  },
  ta: {
    idle: 'தயார்',
    listening: 'கேட்கிறது...',
    transcribing: 'எழுதுகிறது...',
    translating: 'மொழிபெயர்க்கிறது...',
    synthesizing: 'குரல் உருவாக்குகிறது...',
    sending: 'அனுப்புகிறது...',
    error: 'பிழை',
  },
};

/**
 * Conversation UI Component
 */
export const ConversationUI: React.FC<ConversationUIProps> = ({
  userId,
  language,
  onSendMessage,
  onSwitchConversation,
  onEndConversation,
}) => {
  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [processingState, setProcessingState] = useState<ProcessingState>('idle');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Hooks
  const audioFeedback = useAudioFeedback({
    language,
    enabled: true,
    volume: 0.7,
    useTTS: true,
  });
  
  const voiceCommands = useVoiceCommands({
    language,
    confirmationRequired: true,
    onCommandExecuted: handleVoiceCommand,
  });

  /**
   * Handle voice commands
   */
  function handleVoiceCommand(command: any) {
    switch (command.action) {
      case 'switch_conversation':
        handleSwitchConversation();
        break;
      case 'end_conversation':
        if (activeConversationId) {
          handleEndConversation(activeConversationId);
        }
        break;
      case 'replay_message':
        handleReplayLastMessage();
        break;
      default:
        break;
    }
  }

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /**
   * Load conversations
   */
  const loadConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the API
      // For now, we'll use mock data
      const mockConversations: Conversation[] = [
        {
          id: '1',
          participants: [userId, 'user2'],
          commodity: 'Tomatoes',
          status: 'active',
          created_at: new Date().toISOString(),
          message_count: 5,
        },
        {
          id: '2',
          participants: [userId, 'user3'],
          commodity: 'Onions',
          status: 'active',
          created_at: new Date().toISOString(),
          message_count: 3,
        },
      ];
      
      setConversations(mockConversations);
      
      // Set first conversation as active if none selected
      if (!activeConversationId && mockConversations.length > 0) {
        setActiveConversationId(mockConversations[0].id);
      }
    } catch (err) {
      setError('Failed to load conversations');
      await audioFeedback.playStateFeedback('error', 'Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  }, [userId, activeConversationId, audioFeedback]);

  /**
   * Load messages for active conversation
   */
  const loadMessages = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the API
      // For now, we'll use mock data
      const mockMessages: Message[] = [
        {
          id: '1',
          conversation_id: conversationId,
          sender_id: 'user2',
          original_text: 'Hello, I want to buy tomatoes',
          original_language: 'en',
          translated_text: {
            hi: 'नमस्ते, मैं टमाटर खरीदना चाहता हूं',
            te: 'హలో, నేను టమోటాలు కొనాలనుకుంటున్నాను',
          },
          timestamp: new Date().toISOString(),
          message_metadata: {},
        },
        {
          id: '2',
          conversation_id: conversationId,
          sender_id: userId,
          original_text: 'टमाटर 30 रुपये किलो है',
          original_language: 'hi',
          translated_text: {
            en: 'Tomatoes are 30 rupees per kilo',
            te: 'టమోటాలు కిలో 30 రూపాయలు',
          },
          timestamp: new Date().toISOString(),
          message_metadata: {},
        },
      ];
      
      setMessages(mockMessages);
      scrollToBottom();
    } catch (err) {
      setError('Failed to load messages');
      await audioFeedback.playStateFeedback('error', 'Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  }, [userId, audioFeedback, scrollToBottom]);

  /**
   * Switch to a different conversation with voice announcement (Requirement 16.2)
   */
  const handleSwitchConversation = useCallback(async () => {
    if (conversations.length <= 1) {
      await audioFeedback.playCustomMessage('No other conversations available');
      return;
    }
    
    // Find next conversation
    const currentIndex = conversations.findIndex(c => c.id === activeConversationId);
    const nextIndex = (currentIndex + 1) % conversations.length;
    const nextConversation = conversations[nextIndex];
    
    // Announce the switch (Requirement 16.2)
    const otherParticipant = nextConversation.participants.find(p => p !== userId) || 'Unknown';
    const announcement = `Switching to conversation with ${otherParticipant}`;
    await audioFeedback.playCustomMessage(announcement);
    
    // Switch conversation
    setActiveConversationId(nextConversation.id);
    
    if (onSwitchConversation) {
      onSwitchConversation(nextConversation.id);
    }
  }, [conversations, activeConversationId, userId, audioFeedback, onSwitchConversation]);

  /**
   * End the current conversation
   */
  const handleEndConversation = useCallback(async (conversationId: string) => {
    try {
      await audioFeedback.playActionPrompt('end_conversation');
      
      // In a real implementation, this would call the API
      // Update local state
      setConversations(prev => 
        prev.map(c => 
          c.id === conversationId 
            ? { ...c, status: 'completed' as const }
            : c
        )
      );
      
      await audioFeedback.playStateFeedback('success', 'Conversation ended');
      
      if (onEndConversation) {
        onEndConversation(conversationId);
      }
      
      // Switch to another conversation if available
      const activeConvs = conversations.filter(c => c.status === 'active' && c.id !== conversationId);
      if (activeConvs.length > 0) {
        setActiveConversationId(activeConvs[0].id);
      } else {
        setActiveConversationId(null);
      }
    } catch (err) {
      await audioFeedback.playStateFeedback('error', 'Failed to end conversation');
    }
  }, [conversations, audioFeedback, onEndConversation]);

  /**
   * Replay the last message
   */
  const handleReplayLastMessage = useCallback(async () => {
    if (messages.length === 0) {
      await audioFeedback.playCustomMessage('No messages to replay');
      return;
    }
    
    const lastMessage = messages[messages.length - 1];
    const translatedText = lastMessage.translated_text[language] || lastMessage.original_text;
    
    await audioFeedback.playCustomMessage(translatedText);
  }, [messages, language, audioFeedback]);

  /**
   * Send a message
   * Note: This function is available for future use when message input is added
   */
  const handleSendMessage = useCallback(async (text: string) => {
    if (!activeConversationId || !text.trim()) {
      return;
    }
    
    try {
      // Update processing state with visual indicators (Requirement 5.2)
      setProcessingState('transcribing');
      await audioFeedback.playStateFeedback('processing');
      
      // Simulate processing stages
      await new Promise(resolve => setTimeout(resolve, 500));
      setProcessingState('translating');
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setProcessingState('synthesizing');
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setProcessingState('sending');
      
      // In a real implementation, this would call the API
      if (onSendMessage) {
        await onSendMessage(activeConversationId, text, language);
      }
      
      // Add message to local state
      const newMessage: Message = {
        id: Date.now().toString(),
        conversation_id: activeConversationId,
        sender_id: userId,
        original_text: text,
        original_language: language,
        translated_text: {},
        timestamp: new Date().toISOString(),
        message_metadata: {},
      };
      
      setMessages(prev => [...prev, newMessage]);
      scrollToBottom();
      
      setProcessingState('idle');
      await audioFeedback.playStateFeedback('success');
    } catch (err) {
      setProcessingState('error');
      await audioFeedback.playStateFeedback('error', 'Failed to send message');
      
      // Reset to idle after error
      setTimeout(() => setProcessingState('idle'), 2000);
    }
  }, [activeConversationId, userId, language, audioFeedback, onSendMessage, scrollToBottom]);
  
  // Expose handleSendMessage for future use
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _sendMessage = handleSendMessage;

  /**
   * Get processing state message
   */
  const getProcessingMessage = useCallback((state: ProcessingState): string => {
    const messages = PROCESSING_MESSAGES[language] || PROCESSING_MESSAGES['en'];
    return messages[state];
  }, [language]);

  /**
   * Load conversations on mount
   */
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  /**
   * Load messages when active conversation changes
   */
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
    }
  }, [activeConversationId, loadMessages]);

  /**
   * Get active conversation
   */
  const activeConversation = conversations.find(c => c.id === activeConversationId);

  return (
    <div className="conversation-ui" style={styles.container}>
      {/* Header */}
      <div className="conversation-header" style={styles.header}>
        <h2 style={styles.title}>
          {activeConversation?.commodity || 'Conversation'}
        </h2>
        <div className="conversation-count" style={styles.count}>
          {conversations.filter(c => c.status === 'active').length} / 5 active
        </div>
      </div>

      {/* Processing State Indicator (Requirement 5.2) */}
      {processingState !== 'idle' && (
        <div 
          className="processing-indicator" 
          style={{
            ...styles.processingIndicator,
            backgroundColor: processingState === 'error' ? '#fee' : '#e3f2fd',
          }}
        >
          <div className="processing-spinner" style={styles.spinner}>
            {processingState !== 'error' && '⟳'}
            {processingState === 'error' && '⚠'}
          </div>
          <span style={styles.processingText}>
            {getProcessingMessage(processingState)}
          </span>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message" style={styles.error}>
          {error}
        </div>
      )}

      {/* Conversation List */}
      {conversations.length > 1 && (
        <div className="conversation-list" style={styles.conversationList}>
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => setActiveConversationId(conv.id)}
              style={{
                ...styles.conversationButton,
                backgroundColor: conv.id === activeConversationId ? '#2196f3' : '#f5f5f5',
                color: conv.id === activeConversationId ? '#fff' : '#333',
              }}
            >
              <div style={styles.conversationInfo}>
                <strong>{conv.commodity || 'Conversation'}</strong>
                <span style={styles.messageCount}>
                  {conv.message_count} messages
                </span>
              </div>
              {conv.status !== 'active' && (
                <span style={styles.statusBadge}>{conv.status}</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="messages-container" style={styles.messagesContainer}>
        {isLoading && (
          <div style={styles.loadingMessage}>Loading messages...</div>
        )}
        
        {!isLoading && messages.length === 0 && (
          <div style={styles.emptyMessage}>No messages yet</div>
        )}
        
        {messages.map(message => {
          const isOwnMessage = message.sender_id === userId;
          const displayText = message.translated_text[language] || message.original_text;
          
          return (
            <div
              key={message.id}
              className="message"
              style={{
                ...styles.message,
                alignSelf: isOwnMessage ? 'flex-end' : 'flex-start',
                backgroundColor: isOwnMessage ? '#dcf8c6' : '#fff',
              }}
            >
              <div style={styles.messageText}>{displayText}</div>
              <div style={styles.messageTime}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Voice Command Confirmation */}
      {voiceCommands.isWaitingForConfirmation && voiceCommands.confirmationMessage && (
        <div className="confirmation-dialog" style={styles.confirmationDialog}>
          <p style={styles.confirmationText}>{voiceCommands.confirmationMessage}</p>
          <div style={styles.confirmationButtons}>
            <button
              onClick={voiceCommands.confirmPendingCommand}
              style={{ ...styles.button, ...styles.confirmButton }}
            >
              Yes
            </button>
            <button
              onClick={voiceCommands.cancelPendingCommand}
              style={{ ...styles.button, ...styles.cancelButton }}
            >
              No
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-buttons" style={styles.actionButtons}>
        <button
          onClick={handleSwitchConversation}
          disabled={conversations.length <= 1}
          style={{
            ...styles.button,
            ...styles.actionButton,
            opacity: conversations.length <= 1 ? 0.5 : 1,
          }}
        >
          Switch Conversation
        </button>
        
        <button
          onClick={() => activeConversationId && handleEndConversation(activeConversationId)}
          disabled={!activeConversationId}
          style={{
            ...styles.button,
            ...styles.actionButton,
            opacity: !activeConversationId ? 0.5 : 1,
          }}
        >
          End Conversation
        </button>
        
        <button
          onClick={handleReplayLastMessage}
          disabled={messages.length === 0}
          style={{
            ...styles.button,
            ...styles.actionButton,
            opacity: messages.length === 0 ? 0.5 : 1,
          }}
        >
          Replay Last Message
        </button>
      </div>
    </div>
  );
};

/**
 * Styles
 */
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: '#fafafa',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    padding: '16px',
    backgroundColor: '#2196f3',
    color: '#fff',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 'bold',
  },
  count: {
    fontSize: '14px',
    opacity: 0.9,
  },
  processingIndicator: {
    padding: '12px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    borderBottom: '1px solid #ddd',
  },
  spinner: {
    fontSize: '20px',
    animation: 'spin 1s linear infinite',
  },
  processingText: {
    fontSize: '14px',
    fontWeight: '500',
  },
  error: {
    padding: '12px 16px',
    backgroundColor: '#fee',
    color: '#c33',
    borderBottom: '1px solid #fcc',
  },
  conversationList: {
    display: 'flex',
    gap: '8px',
    padding: '12px 16px',
    overflowX: 'auto',
    borderBottom: '1px solid #ddd',
    backgroundColor: '#fff',
  },
  conversationButton: {
    padding: '12px 16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    minWidth: '150px',
    textAlign: 'left',
    transition: 'all 0.2s',
    fontSize: '14px',
  },
  conversationInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  messageCount: {
    fontSize: '12px',
    opacity: 0.7,
  },
  statusBadge: {
    fontSize: '11px',
    padding: '2px 6px',
    borderRadius: '4px',
    backgroundColor: 'rgba(0,0,0,0.1)',
    marginTop: '4px',
    display: 'inline-block',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  loadingMessage: {
    textAlign: 'center',
    color: '#666',
    padding: '20px',
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#999',
    padding: '40px 20px',
    fontSize: '16px',
  },
  message: {
    maxWidth: '70%',
    padding: '12px 16px',
    borderRadius: '12px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
  },
  messageText: {
    fontSize: '15px',
    lineHeight: '1.4',
    marginBottom: '4px',
  },
  messageTime: {
    fontSize: '11px',
    opacity: 0.6,
    textAlign: 'right',
  },
  confirmationDialog: {
    padding: '16px',
    backgroundColor: '#fff3cd',
    borderTop: '1px solid #ffc107',
    borderBottom: '1px solid #ffc107',
  },
  confirmationText: {
    margin: '0 0 12px 0',
    fontSize: '15px',
    fontWeight: '500',
  },
  confirmationButtons: {
    display: 'flex',
    gap: '12px',
  },
  actionButtons: {
    padding: '16px',
    display: 'flex',
    gap: '12px',
    backgroundColor: '#fff',
    borderTop: '1px solid #ddd',
  },
  button: {
    padding: '12px 20px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#2196f3',
    color: '#fff',
  },
  confirmButton: {
    flex: 1,
    backgroundColor: '#4caf50',
    color: '#fff',
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#f44336',
    color: '#fff',
  },
};

export default ConversationUI;
