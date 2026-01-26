/**
 * AudioDemo Component - Demonstrates audio capture, compression, and playback
 */

import { useState, useEffect, useRef } from 'react';
import { AudioCaptureModule } from '../services/audio/AudioCaptureModule';
import { AudioCompressionModule } from '../services/audio/AudioCompressionModule';
import { AudioPlaybackModule } from '../services/audio/AudioPlaybackModule';

export const AudioDemo = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [ambientNoise, setAmbientNoise] = useState(50);
  const [compressionRatio, setCompressionRatio] = useState(0);
  const [networkQuality, setNetworkQuality] = useState('fair');
  
  const captureModule = useRef<AudioCaptureModule | null>(null);
  const compressionModule = useRef<AudioCompressionModule | null>(null);
  const playbackModule = useRef<AudioPlaybackModule | null>(null);
  const lastAudioBlob = useRef<Blob | null>(null);

  useEffect(() => {
    // Initialize modules
    const initModules = async () => {
      captureModule.current = new AudioCaptureModule();
      compressionModule.current = new AudioCompressionModule();
      playbackModule.current = new AudioPlaybackModule();
      
      try {
        await captureModule.current.initialize();
        await playbackModule.current.initialize();
      } catch (error) {
        console.error('Failed to initialize audio modules:', error);
      }
    };

    initModules();

    // Cleanup on unmount
    return () => {
      captureModule.current?.cleanup();
      compressionModule.current?.cleanup();
      playbackModule.current?.cleanup();
    };
  }, []);

  const handleRecord = async () => {
    if (!captureModule.current || !compressionModule.current) return;

    try {
      setIsRecording(true);
      
      // Capture 5 seconds of audio
      const audio = await captureModule.current.captureAndProcess(5000);
      
      // Compress audio
      const result = await compressionModule.current.compressWithAdaptiveBitrate(audio);
      
      setCompressionRatio(result.compressionRatio);
      lastAudioBlob.current = result.compressedData;
      
      setIsRecording(false);
      
      console.log(`Audio captured and compressed: ${result.compressionRatio.toFixed(1)}% reduction`);
    } catch (error) {
      console.error('Recording failed:', error);
      setIsRecording(false);
    }
  };

  const handlePlay = async () => {
    if (!playbackModule.current || !lastAudioBlob.current) return;

    try {
      setIsPlaying(true);
      await playbackModule.current.playAudio(lastAudioBlob.current);
      setIsPlaying(false);
    } catch (error) {
      console.error('Playback failed:', error);
      setIsPlaying(false);
    }
  };

  const handleReplay = async () => {
    if (!playbackModule.current) return;

    try {
      setIsPlaying(true);
      await playbackModule.current.replay();
      setIsPlaying(false);
    } catch (error) {
      console.error('Replay failed:', error);
      setIsPlaying(false);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    playbackModule.current?.setVolume(newVolume);
  };

  const handleDetectNoise = async () => {
    if (!playbackModule.current) return;

    try {
      const noise = await playbackModule.current.detectAmbientNoise();
      setAmbientNoise(Math.round(noise));
    } catch (error) {
      console.error('Noise detection failed:', error);
    }
  };

  const handleDetectNetwork = async () => {
    if (!compressionModule.current) return;

    try {
      const condition = await compressionModule.current.detectNetworkCondition();
      setNetworkQuality(condition.quality);
    } catch (error) {
      console.error('Network detection failed:', error);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Audio Capture & Processing Demo</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Audio Capture</h3>
        <button 
          onClick={handleRecord} 
          disabled={isRecording}
          style={{ padding: '10px 20px', marginRight: '10px' }}
        >
          {isRecording ? 'Recording...' : 'Record 5s'}
        </button>
        {compressionRatio > 0 && (
          <span>Compression: {compressionRatio.toFixed(1)}%</span>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Audio Playback</h3>
        <button 
          onClick={handlePlay} 
          disabled={!lastAudioBlob.current || isPlaying}
          style={{ padding: '10px 20px', marginRight: '10px' }}
        >
          {isPlaying ? 'Playing...' : 'Play'}
        </button>
        <button 
          onClick={handleReplay} 
          disabled={!playbackModule.current?.canReplay() || isPlaying}
          style={{ padding: '10px 20px' }}
        >
          Replay
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Volume Control</h3>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.1" 
          value={volume}
          onChange={handleVolumeChange}
          style={{ width: '200px' }}
        />
        <span style={{ marginLeft: '10px' }}>{(volume * 100).toFixed(0)}%</span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Ambient Noise Detection</h3>
        <button 
          onClick={handleDetectNoise}
          style={{ padding: '10px 20px', marginRight: '10px' }}
        >
          Detect Noise
        </button>
        <span>Level: {ambientNoise} dB</span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Network Condition</h3>
        <button 
          onClick={handleDetectNetwork}
          style={{ padding: '10px 20px', marginRight: '10px' }}
        >
          Detect Network
        </button>
        <span>Quality: {networkQuality}</span>
      </div>

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
        <h4>Features Implemented:</h4>
        <ul>
          <li>✓ Microphone access with Web Audio API</li>
          <li>✓ Voice Activity Detection (VAD)</li>
          <li>✓ Noise reduction using spectral subtraction</li>
          <li>✓ Audio compression with Opus codec (60%+ reduction)</li>
          <li>✓ Adaptive bitrate based on network speed</li>
          <li>✓ TTS audio playback</li>
          <li>✓ Adaptive volume based on ambient noise</li>
          <li>✓ Replay functionality</li>
        </ul>
      </div>
    </div>
  );
};
