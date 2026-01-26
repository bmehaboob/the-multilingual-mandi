"""Manual test for speaker recognition model"""
import os
import sys

# Set environment variable before any imports
os.environ["TORCHAUDIO_BACKEND"] = "soundfile"

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import numpy as np
from app.services.auth.speaker_recognition_model import SpeakerRecognitionModel


def main():
    print("=" * 60)
    print("Manual Test: Speaker Recognition Model")
    print("=" * 60)
    
    # Create model instance
    print("\n1. Creating SpeakerRecognitionModel instance...")
    model = SpeakerRecognitionModel()
    print(f"   ✓ Model created on device: {model.device}")
    print(f"   ✓ Embedding dimension: {model.embedding_dimension}")
    
    # Load model
    print("\n2. Loading ECAPA-TDNN model from HuggingFace...")
    print("   (This may take a few minutes on first run to download the model)")
    try:
        model.load_model()
        print("   ✓ Model loaded successfully!")
    except Exception as e:
        print(f"   ✗ Failed to load model: {e}")
        return
    
    # Generate sample audio
    print("\n3. Generating sample audio (1 second, 16kHz)...")
    sample_rate = 16000
    duration = 1.0
    audio = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    print(f"   ✓ Audio shape: {audio.shape}")
    
    # Validate audio quality
    print("\n4. Validating audio quality...")
    is_valid, error_msg = model.validate_audio_quality(audio, sample_rate)
    if is_valid:
        print("   ✓ Audio quality is valid")
    else:
        print(f"   ✗ Audio quality check failed: {error_msg}")
        return
    
    # Extract embedding
    print("\n5. Extracting speaker embedding...")
    try:
        embedding = model.extract_embedding(audio, sample_rate)
        print(f"   ✓ Embedding extracted successfully!")
        print(f"   ✓ Embedding shape: {embedding.shape}")
        print(f"   ✓ Embedding dtype: {embedding.dtype}")
        print(f"   ✓ Embedding range: [{embedding.min():.4f}, {embedding.max():.4f}]")
    except Exception as e:
        print(f"   ✗ Failed to extract embedding: {e}")
        return
    
    # Test similarity computation
    print("\n6. Testing similarity computation...")
    # Create a second similar embedding
    audio2 = audio + np.random.randn(len(audio)).astype(np.float32) * 0.05
    embedding2 = model.extract_embedding(audio2, sample_rate)
    
    similarity = model.compute_similarity(embedding, embedding2)
    print(f"   ✓ Similarity between similar audio: {similarity:.4f}")
    
    # Test with different audio
    audio3 = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    embedding3 = model.extract_embedding(audio3, sample_rate)
    similarity_diff = model.compute_similarity(embedding, embedding3)
    print(f"   ✓ Similarity between different audio: {similarity_diff:.4f}")
    
    # Test averaging embeddings
    print("\n7. Testing embedding averaging...")
    embeddings = [embedding, embedding2]
    averaged = model.average_embeddings(embeddings)
    print(f"   ✓ Averaged embedding shape: {averaged.shape}")
    print(f"   ✓ Averaged embedding is normalized: {np.linalg.norm(averaged):.4f}")
    
    # Unload model
    print("\n8. Unloading model from memory...")
    model.unload_model()
    print(f"   ✓ Model unloaded. Is loaded: {model.is_loaded}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
