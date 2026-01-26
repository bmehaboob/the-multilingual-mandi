/**
 * Audio Feedback Demo Component
 * 
 * Demonstrates the audio feedback system with all system states and action prompts
 */

import React, { useState } from 'react';
import { useAudioFeedback } from '../services/audio/useAudioFeedback';
import { SystemState, ActionPrompt } from '../services/audio/AudioFeedbackSystem';

export const AudioFeedbackDemo: React.FC = () => {
  const [language, setLanguage] = useState('en');
  const [enabled, setEnabled] = useState(true);
  const [volume, setVolume] = useState(0.7);
  const [customMessage, setCustomMessage] = useState('');

  const audioFeedback = useAudioFeedback({
    language,
    enabled,
    volume,
    useTTS: true,
  });

  const systemStates: SystemState[] = [
    'loading',
    'success',
    'error',
    'warning',
    'info',
    'processing',
    'connecting',
    'offline',
    'online',
  ];

  const actionPrompts: ActionPrompt[] = [
    'start_conversation',
    'check_price',
    'request_negotiation',
    'end_conversation',
    'switch_conversation',
    'view_history',
    'replay_message',
    'confirm_action',
    'cancel_action',
    'welcome',
    'goodbye',
  ];

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi (हिंदी)' },
    { code: 'te', name: 'Telugu (తెలుగు)' },
    { code: 'ta', name: 'Tamil (தமிழ்)' },
    { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
    { code: 'mr', name: 'Marathi (मराठी)' },
  ];

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLanguage = e.target.value;
    setLanguage(newLanguage);
    audioFeedback.setLanguage(newLanguage);
  };

  const handleEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabled = e.target.checked;
    setEnabled(newEnabled);
    audioFeedback.setEnabled(newEnabled);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    audioFeedback.setVolume(newVolume);
  };

  const handlePlayState = (state: SystemState) => {
    audioFeedback.playStateFeedback(state);
  };

  const handlePlayAction = (action: ActionPrompt) => {
    audioFeedback.playActionPrompt(action);
  };

  const handlePlayCustom = () => {
    if (customMessage.trim()) {
      audioFeedback.playCustomMessage(customMessage);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Audio Feedback System Demo</h1>
      
      {!audioFeedback.isInitialized && (
        <div style={{ padding: '10px', background: '#fff3cd', marginBottom: '20px' }}>
          Initializing audio feedback system...
        </div>
      )}

      {audioFeedback.isPlaying && (
        <div style={{ padding: '10px', background: '#d1ecf1', marginBottom: '20px' }}>
          🔊 Playing audio feedback...
        </div>
      )}

      <div style={{ marginBottom: '30px', padding: '15px', background: '#f8f9fa', borderRadius: '5px' }}>
        <h2>Settings</h2>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Language:
            <select 
              value={language} 
              onChange={handleLanguageChange}
              style={{ marginLeft: '10px', padding: '5px' }}
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            <input 
              type="checkbox" 
              checked={enabled} 
              onChange={handleEnabledChange}
              style={{ marginRight: '5px' }}
            />
            Enable Audio Feedback
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Volume: {volume.toFixed(2)}
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.1" 
              value={volume}
              onChange={handleVolumeChange}
              style={{ marginLeft: '10px', width: '200px' }}
            />
          </label>
        </div>

        <div>
          <button 
            onClick={() => audioFeedback.stop()}
            style={{ padding: '8px 15px', marginRight: '10px' }}
          >
            Stop
          </button>
          <button 
            onClick={() => audioFeedback.clearQueue()}
            style={{ padding: '8px 15px' }}
          >
            Clear Queue
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h2>System States (Requirement 11.4)</h2>
        <p>Click to play audio feedback for different system states:</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          {systemStates.map(state => (
            <button
              key={state}
              onClick={() => handlePlayState(state)}
              disabled={!audioFeedback.isInitialized || !enabled}
              style={{
                padding: '10px',
                background: getStateColor(state),
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: enabled ? 'pointer' : 'not-allowed',
                opacity: enabled ? 1 : 0.5,
              }}
            >
              {state}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h2>Action Prompts (Requirement 11.1)</h2>
        <p>Click to play voice prompts for major actions:</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          {actionPrompts.map(action => (
            <button
              key={action}
              onClick={() => handlePlayAction(action)}
              disabled={!audioFeedback.isInitialized || !enabled}
              style={{
                padding: '10px',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: enabled ? 'pointer' : 'not-allowed',
                opacity: enabled ? 1 : 0.5,
              }}
            >
              {action.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h2>Custom Message</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="Enter custom message"
            style={{ flex: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
          <button
            onClick={handlePlayCustom}
            disabled={!audioFeedback.isInitialized || !enabled || !customMessage.trim()}
            style={{
              padding: '10px 20px',
              background: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: enabled && customMessage.trim() ? 'pointer' : 'not-allowed',
              opacity: enabled && customMessage.trim() ? 1 : 0.5,
            }}
          >
            Play Custom
          </button>
        </div>
      </div>

      <div style={{ padding: '15px', background: '#e9ecef', borderRadius: '5px' }}>
        <h3>About Audio Feedback System</h3>
        <ul>
          <li>Provides audio feedback for all system states (loading, error, success, etc.)</li>
          <li>Offers voice prompts for all major actions</li>
          <li>Supports multiple Indian languages (Hindi, Telugu, Tamil, Kannada, Marathi, etc.)</li>
          <li>Uses tone feedback for quick state indication</li>
          <li>Uses Text-to-Speech for voice prompts</li>
          <li>Queues feedback when multiple events occur</li>
          <li>Adjustable volume and language settings</li>
        </ul>
      </div>
    </div>
  );
};

function getStateColor(state: SystemState): string {
  const colors: Record<SystemState, string> = {
    loading: '#6c757d',
    success: '#28a745',
    error: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    processing: '#6610f2',
    connecting: '#007bff',
    offline: '#6c757d',
    online: '#28a745',
  };
  return colors[state];
}
