/**
 * Vitest setup file
 * Configures test environment and mocks
 */

import { vi } from 'vitest';

// Mock Web Audio API
global.AudioContext = vi.fn().mockImplementation(() => ({
  createAnalyser: vi.fn(() => ({
    fftSize: 2048,
    smoothingTimeConstant: 0.8,
    frequencyBinCount: 1024,
    connect: vi.fn(),
    getByteFrequencyData: vi.fn((array) => {
      // Fill with mock data
      for (let i = 0; i < array.length; i++) {
        array[i] = 50 + Math.random() * 50;
      }
    }),
  })),
  createMediaStreamSource: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  })),
  createScriptProcessor: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    onaudioprocess: null,
  })),
  createBuffer: vi.fn((channels, length, sampleRate) => ({
    copyToChannel: vi.fn(),
    getChannelData: vi.fn(() => new Float32Array(length)),
    duration: length / sampleRate,
  })),
  createBufferSource: vi.fn(() => ({
    buffer: null,
    playbackRate: { value: 1.0 },
    loop: false,
    connect: vi.fn(),
    disconnect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    onended: null,
  })),
  createGain: vi.fn(() => ({
    gain: { value: 0.7 },
    connect: vi.fn(),
  })),
  createMediaStreamDestination: vi.fn(() => ({
    stream: {
      getTracks: vi.fn(() => [{ stop: vi.fn() }]),
    },
  })),
  decodeAudioData: vi.fn((arrayBuffer) => {
    return Promise.resolve({
      duration: 1.0,
      length: 16000,
      sampleRate: 16000,
      numberOfChannels: 1,
      getChannelData: vi.fn(() => new Float32Array(16000)),
    });
  }),
  destination: {},
  sampleRate: 16000,
  currentTime: 0,
  state: 'running',
  close: vi.fn().mockResolvedValue(undefined),
})) as any;

// Mock OfflineAudioContext
global.OfflineAudioContext = vi.fn().mockImplementation(() => ({
  createBuffer: vi.fn((channels, length, sampleRate) => ({
    copyToChannel: vi.fn(),
  })),
  createBufferSource: vi.fn(() => ({
    buffer: null,
    connect: vi.fn(),
  })),
  destination: {},
  sampleRate: 16000,
})) as any;

// Mock MediaDevices API
Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: vi.fn(() => [
        {
          stop: vi.fn(),
        },
      ]),
    }),
  },
});

// Mock MediaRecorder
global.MediaRecorder = vi.fn().mockImplementation((stream, options) => ({
  start: vi.fn(),
  stop: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onstop: null,
  onerror: null,
})) as any;

MediaRecorder.isTypeSupported = vi.fn((type: string) => {
  return type.includes('webm') || type.includes('opus');
});

// Mock fetch for network tests
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
});

// Mock performance.now
global.performance = {
  now: vi.fn(() => Date.now()),
} as any;


