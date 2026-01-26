"""Voice biometric enrollment service"""
import logging
from typing import List, Optional
from datetime import datetime
import numpy as np
import uuid
from cryptography.fernet import Fernet
import os

from .speaker_recognition_model import SpeakerRecognitionModel
from .models import VoiceprintID, EnrollmentResult, VoiceSample

logger = logging.getLogger(__name__)


class VoiceBiometricEnrollment:
    def __init__(self, speaker_model=None, encryption_key=None, min_samples=3, max_samples=5, quality_threshold=0.7):
        self.speaker_model = speaker_model or SpeakerRecognitionModel()
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.quality_threshold = quality_threshold
        if encryption_key is None:
            encryption_key = os.getenv("VOICEPRINT_ENCRYPTION_KEY")
            if encryption_key:
                encryption_key = encryption_key.encode()
            else:
                encryption_key = Fernet.generate_key()
                logger.warning("No encryption key provided.")
        self.cipher = Fernet(encryption_key)
        self._voiceprint_storage = {}
    
    def enroll_user(self, user_id, voice_samples):
        logger.info(f"Starting enrollment for user {user_id}")
        if len(voice_samples) < self.min_samples:
            return EnrollmentResult(voiceprint_id=None, success=False, num_samples_used=0, quality_score=0.0, message="Insufficient samples")
        if len(voice_samples) > self.max_samples:
            voice_samples = voice_samples[:self.max_samples]
        if not self.speaker_model.is_loaded:
            self.speaker_model.load_model()
        embeddings = []
        quality_scores = []
        for i, sample in enumerate(voice_samples):
            try:
                audio_array = self._bytes_to_audio(sample.audio, sample.sample_rate)
                is_valid, error_msg = self.speaker_model.validate_audio_quality(audio_array, sample.sample_rate)
                if not is_valid:
                    continue
                embedding = self.speaker_model.extract_embedding(audio_array, sample.sample_rate)
                quality_score = self._calculate_quality_score(embedding)
                if quality_score < self.quality_threshold:
                    continue
                embeddings.append(embedding)
                quality_scores.append(quality_score)
            except Exception as e:
                continue
        if len(embeddings) < self.min_samples:
            return EnrollmentResult(voiceprint_id=None, success=False, num_samples_used=len(embeddings), quality_score=np.mean(quality_scores) if quality_scores else 0.0, message="Insufficient valid samples")
        try:
            voiceprint = self.speaker_model.average_embeddings(embeddings)
            overall_quality = float(np.mean(quality_scores))
            voiceprint_id = self._store_voiceprint(user_id, voiceprint, overall_quality)
            return EnrollmentResult(voiceprint_id=voiceprint_id, success=True, num_samples_used=len(embeddings), quality_score=overall_quality, message="Enrollment successful")
        except Exception as e:
            return EnrollmentResult(voiceprint_id=None, success=False, num_samples_used=len(embeddings), quality_score=np.mean(quality_scores) if quality_scores else 0.0, message=f"Failed: {str(e)}")
    
    def _bytes_to_audio(self, audio_bytes, sample_rate):
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_array.astype(np.float32) / 32768.0
    
    def _calculate_quality_score(self, embedding):
        magnitude = np.linalg.norm(embedding)
        magnitude_score = 1.0 - abs(1.0 - magnitude)
        variance = np.var(embedding)
        variance_score = min(variance * 10, 1.0)
        return float(magnitude_score * 0.6 + variance_score * 0.4)
    
    def _store_voiceprint(self, user_id, voiceprint, quality_score):
        voiceprint_uuid = str(uuid.uuid4())
        voiceprint_bytes = voiceprint.tobytes()
        encrypted_voiceprint = self.cipher.encrypt(voiceprint_bytes)
        now = datetime.utcnow()
        voiceprint_id = VoiceprintID(id=voiceprint_uuid, user_id=user_id, created_at=now, updated_at=now)
        self._voiceprint_storage[voiceprint_uuid] = {"user_id": user_id, "encrypted_voiceprint": encrypted_voiceprint, "quality_score": quality_score, "embedding_shape": voiceprint.shape, "created_at": now, "updated_at": now}
        return voiceprint_id
    
    def get_voiceprint(self, voiceprint_id):
        if voiceprint_id not in self._voiceprint_storage:
            return None
        try:
            stored_data = self._voiceprint_storage[voiceprint_id]
            voiceprint_bytes = self.cipher.decrypt(stored_data["encrypted_voiceprint"])
            voiceprint = np.frombuffer(voiceprint_bytes, dtype=np.float64)
            return voiceprint.reshape(stored_data["embedding_shape"])
        except Exception as e:
            return None
    
    def get_voiceprint_by_user(self, user_id):
        for voiceprint_id, data in self._voiceprint_storage.items():
            if data["user_id"] == user_id:
                return self.get_voiceprint(voiceprint_id)
        return None
    
    def update_voiceprint(self, user_id, voice_samples):
        for voiceprint_id, data in self._voiceprint_storage.items():
            if data["user_id"] == user_id:
                del self._voiceprint_storage[voiceprint_id]
                break
        return self.enroll_user(user_id, voice_samples)
    
    def delete_voiceprint(self, user_id):
        for voiceprint_id, data in list(self._voiceprint_storage.items()):
            if data["user_id"] == user_id:
                del self._voiceprint_storage[voiceprint_id]
                return True
        return False
    
    def get_enrollment_stats(self):
        if not self._voiceprint_storage:
            return {"total_voiceprints": 0, "average_quality": 0.0, "unique_users": 0}
        quality_scores = [data["quality_score"] for data in self._voiceprint_storage.values()]
        unique_users = len(set(data["user_id"] for data in self._voiceprint_storage.values()))
        return {"total_voiceprints": len(self._voiceprint_storage), "average_quality": float(np.mean(quality_scores)), "unique_users": unique_users}
