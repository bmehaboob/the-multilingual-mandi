"""Pytest configuration for tests"""
import os
import sys

# Set torchaudio backend before any imports
# This fixes compatibility issues with SpeechBrain and newer torchaudio versions
os.environ["TORCHAUDIO_BACKEND"] = "soundfile"

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENVIRONMENT"] = "test"

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
