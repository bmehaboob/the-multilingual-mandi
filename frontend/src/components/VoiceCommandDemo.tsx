/**
 * Voice Command Demo Component
 * 
 * Demonstrates the voice command handler with confirmation flow
 * Requirements: 11.2, 11.3
 */

import React, { useState } from 'react';
import { useVoiceCommands } from '../services/voice/useVoiceCommands';
import { VoiceCommand } from '../services/voice/VoiceCommandHandler';

export const VoiceCommandDemo: React.FC = () => {
  const [language, setLanguage] = useState('en');
  const [confirmationRequired, setConfirmationRequired] = useState(true);
  const [voiceInput, setVoiceInput] = useState('');
  const [executedCommands, setExecutedCommands] = useState<VoiceCommand[]>([]);
  const [status, setStatus] = useState<string>('');

  const {
    processVoiceInput,
    confirmPendingCommand,
    cancelPendingCommand,
    pendingCommand,
    isWaitingForConfirmation,
    confirmationMessage,
    setLanguage: updateLanguage,
    setConfirmationRequired: updateConfirmationRequired,
  } = useVoiceCommands({
    language,
    confirmationRequired,
    onCommandExecuted: (command) => {
      setExecutedCommands((prev) => [...prev, command]);
      setStatus(`Executed: ${command.action}`);
    },
    onError: (error) => {
      setStatus(`Error: ${error.message}`);
    },
  });

  const handleLanguageChange = (newLanguage: string) => {
    setLanguage(newLanguage);
    updateLanguage(newLanguage);
  };

  const handleConfirmationToggle = () => {
    const newValue = !confirmationRequired;
    setConfirmationRequired(newValue);
    updateConfirmationRequired(newValue);
  };

  const handleProcessInput = async () => {
    if (!voiceInput.trim()) return;
    setStatus('Processing...');
    await processVoiceInput(voiceInput, language);
    setVoiceInput('');
  };

  const handleConfirm = async () => {
    await confirmPendingCommand();
  };

  const handleCancel = () => {
    cancelPendingCommand();
    setStatus('Command cancelled');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Voice Command Handler Demo</h1>
      
      {/* Settings */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Settings</h2>
        <div style={{ marginBottom: '10px' }}>
          <label>
            Language:{' '}
            <select value={language} onChange={(e) => handleLanguageChange(e.target.value)}>
              <option value="en">English</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="ta">Tamil (தமிழ்)</option>
            </select>
          </label>
        </div>
        <div>
          <label>
            <input
              type="checkbox"
              checked={confirmationRequired}
              onChange={handleConfirmationToggle}
            />
            {' '}Require Confirmation
          </label>
        </div>
      </div>

      {/* Voice Input */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Voice Input</h2>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="text"
            value={voiceInput}
            onChange={(e) => setVoiceInput(e.target.value)}
            placeholder="Enter voice command..."
            style={{ width: '100%', padding: '8px', fontSize: '16px' }}
            onKeyPress={(e) => e.key === 'Enter' && handleProcessInput()}
          />
        </div>
        <button
          onClick={handleProcessInput}
          style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
        >
          Process Command
        </button>
        
        {/* Example Commands */}
        <div style={{ marginTop: '15px', fontSize: '14px', color: '#666' }}>
          <strong>Example commands:</strong>
          <ul style={{ marginTop: '5px' }}>
            {language === 'en' && (
              <>
                <li>go home</li>
                <li>check prices</li>
                <li>start conversation</li>
                <li>help</li>
              </>
            )}
            {language === 'hi' && (
              <>
                <li>होम पर जाओ</li>
                <li>कीमत जांचो</li>
                <li>बातचीत शुरू करो</li>
                <li>मदद</li>
              </>
            )}
            {language === 'te' && (
              <>
                <li>హోమ్‌కు వెళ్ళు</li>
                <li>ధర తనిఖీ చేయి</li>
                <li>సంభాషణ ప్రారంభించు</li>
                <li>సహాయం</li>
              </>
            )}
            {language === 'ta' && (
              <>
                <li>முகப்புக்கு செல்</li>
                <li>விலை சரிபார்</li>
                <li>உரையாடல் தொடங்கு</li>
                <li>உதவி</li>
              </>
            )}
          </ul>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {isWaitingForConfirmation && pendingCommand && (
        <div
          style={{
            marginBottom: '20px',
            padding: '15px',
            border: '2px solid #ff9800',
            borderRadius: '5px',
            backgroundColor: '#fff3e0',
          }}
        >
          <h2>Confirmation Required</h2>
          <p style={{ fontSize: '18px', marginBottom: '15px' }}>
            <strong>{confirmationMessage}</strong>
          </p>
          <div>
            <button
              onClick={handleConfirm}
              style={{
                padding: '10px 20px',
                fontSize: '16px',
                marginRight: '10px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
              }}
            >
              {language === 'hi' ? 'हां' : language === 'te' ? 'అవును' : language === 'ta' ? 'ஆம்' : 'Yes'}
            </button>
            <button
              onClick={handleCancel}
              style={{
                padding: '10px 20px',
                fontSize: '16px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
              }}
            >
              {language === 'hi' ? 'नहीं' : language === 'te' ? 'కాదు' : language === 'ta' ? 'இல்லை' : 'No'}
            </button>
          </div>
          <p style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
            Or say "yes" / "no" to confirm/cancel
          </p>
        </div>
      )}

      {/* Status */}
      {status && (
        <div
          style={{
            marginBottom: '20px',
            padding: '10px',
            border: '1px solid #2196f3',
            borderRadius: '5px',
            backgroundColor: '#e3f2fd',
          }}
        >
          <strong>Status:</strong> {status}
        </div>
      )}

      {/* Executed Commands */}
      <div style={{ padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Executed Commands</h2>
        {executedCommands.length === 0 ? (
          <p style={{ color: '#666' }}>No commands executed yet</p>
        ) : (
          <ul>
            {executedCommands.map((cmd, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>
                <strong>{cmd.action}</strong> (Language: {cmd.language}, Confidence: {(cmd.confidence * 100).toFixed(0)}%)
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
