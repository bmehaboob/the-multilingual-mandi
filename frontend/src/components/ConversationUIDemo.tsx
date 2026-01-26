/**
 * Conversation UI Demo Component
 * 
 * Demonstrates the voice-first conversation interface with visual indicators
 * and conversation switching capabilities.
 */

import React, { useState } from 'react';
import { ConversationUI } from './ConversationUI';

export const ConversationUIDemo: React.FC = () => {
  const [language, setLanguage] = useState('en');
  const [userId] = useState('demo-user-1');

  const handleSendMessage = async (conversationId: string, text: string, lang: string) => {
    console.log('Sending message:', { conversationId, text, lang });
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const handleSwitchConversation = (conversationId: string) => {
    console.log('Switched to conversation:', conversationId);
  };

  const handleEndConversation = (conversationId: string) => {
    console.log('Ended conversation:', conversationId);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Conversation UI Demo</h1>
        <div style={styles.languageSelector}>
          <label style={styles.label}>Language: </label>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            style={styles.select}
          >
            <option value="en">English</option>
            <option value="hi">Hindi (हिंदी)</option>
            <option value="te">Telugu (తెలుగు)</option>
            <option value="ta">Tamil (தமிழ்)</option>
          </select>
        </div>
      </div>

      <div style={styles.description}>
        <h2 style={styles.subtitle}>Features Demonstrated:</h2>
        <ul style={styles.featureList}>
          <li>✓ Voice-first conversation interface</li>
          <li>✓ Visual indicators for processing states (transcribing, translating, synthesizing)</li>
          <li>✓ Conversation switching with voice announcements</li>
          <li>✓ Integration with voice command handler</li>
          <li>✓ Integration with audio feedback system</li>
          <li>✓ Support for up to 5 concurrent conversations</li>
          <li>✓ Multilingual support (22 Indian languages)</li>
        </ul>
      </div>

      <div style={styles.demoArea}>
        <ConversationUI
          userId={userId}
          language={language}
          onSendMessage={handleSendMessage}
          onSwitchConversation={handleSwitchConversation}
          onEndConversation={handleEndConversation}
        />
      </div>

      <div style={styles.instructions}>
        <h3 style={styles.subtitle}>Instructions:</h3>
        <ol style={styles.instructionList}>
          <li>The conversation UI displays active conversations at the top</li>
          <li>Click "Switch Conversation" to move between conversations (with voice announcement)</li>
          <li>Click "Replay Last Message" to hear the last message again</li>
          <li>Click "End Conversation" to complete the current conversation</li>
          <li>Processing states are shown when messages are being processed</li>
          <li>Change the language selector to see multilingual support</li>
        </ol>
      </div>

      <div style={styles.requirements}>
        <h3 style={styles.subtitle}>Requirements Validated:</h3>
        <ul style={styles.requirementList}>
          <li><strong>Requirement 5.2:</strong> Visual indicators for processing states</li>
          <li><strong>Requirement 16.2:</strong> Conversation switching with voice announcements</li>
          <li><strong>Requirement 16.4:</strong> Voice-first conversation interface</li>
        </ul>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '20px',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
  },
  title: {
    margin: 0,
    fontSize: '24px',
    color: '#333',
  },
  languageSelector: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
  },
  select: {
    padding: '8px 12px',
    fontSize: '14px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    backgroundColor: '#fff',
  },
  description: {
    marginBottom: '20px',
    padding: '20px',
    backgroundColor: '#e3f2fd',
    borderRadius: '8px',
  },
  subtitle: {
    marginTop: 0,
    marginBottom: '12px',
    fontSize: '18px',
    color: '#1976d2',
  },
  featureList: {
    margin: 0,
    paddingLeft: '20px',
    lineHeight: '1.8',
  },
  demoArea: {
    marginBottom: '20px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  instructions: {
    marginBottom: '20px',
    padding: '20px',
    backgroundColor: '#fff3cd',
    borderRadius: '8px',
  },
  instructionList: {
    margin: 0,
    paddingLeft: '20px',
    lineHeight: '1.8',
  },
  requirements: {
    padding: '20px',
    backgroundColor: '#d4edda',
    borderRadius: '8px',
  },
  requirementList: {
    margin: 0,
    paddingLeft: '20px',
    lineHeight: '1.8',
  },
};

export default ConversationUIDemo;
