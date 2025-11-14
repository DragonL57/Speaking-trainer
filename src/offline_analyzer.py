"""Offline pronunciation analysis using Whisper, librosa, and phonemizer."""

import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import os
from pathlib import Path

# Lazy imports for heavy libraries
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class OfflinePronunciationAnalyzer:
    """Offline pronunciation analyzer using open-source models."""
    
    def __init__(self, whisper_model: str = "base", device: str = "cpu"):
        """Initialize the offline analyzer.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            device: Device to run models on (cpu, cuda)
        """
        self.whisper_model_name = whisper_model
        self.device = device
        self._whisper_model = None
        self._phonemizer = None
        self._wav2vec_model = None
        self._wav2vec_processor = None
        self._pronunciation_quality_logits = None  # Store pronunciation quality scores
        
        logger.info(f"Initialized offline analyzer with Whisper model: {whisper_model}")
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.whisper_model_name}")
                self._whisper_model = whisper.load_model(self.whisper_model_name, device=self.device)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        return self._whisper_model
    
    @property
    def phonemizer(self):
        """Lazy load phonemizer."""
        if self._phonemizer is None:
            try:
                # Try using eng-to-ipa first (simpler, no system dependencies)
                import eng_to_ipa as ipa
                self._phonemizer = lambda text, **kwargs: ipa.convert(text)
                logger.info("Using eng-to-ipa for phoneme conversion")
            except ImportError:
                try:
                    # Fallback to phonemizer if available and espeak installed
                    from phonemizer import phonemize
                    self._phonemizer = phonemize
                    logger.info("Using phonemizer with espeak")
                except Exception as e:
                    logger.error(f"Failed to load phonemizer: {e}")
                    # Ultimate fallback: basic character-based
                    def basic_phonemizer(text, **kwargs):
                        # Simple character-to-phoneme approximation
                        import re
                        # Remove punctuation and convert to uppercase
                        cleaned = re.sub(r'[^\w\s]', '', text.upper())
                        # Split into characters as basic "phonemes"
                        return ' '.join(list(cleaned.replace(' ', '')))
                    self._phonemizer = basic_phonemizer
                    logger.warning("Using basic fallback phonemizer")
        return self._phonemizer
    
    @property
    def wav2vec_model(self):
        """Lazy load wav2vec2 model for pronunciation evaluation."""
        if self._wav2vec_model is None:
            try:
                from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
                # Use pronunciation evaluation fine-tuned model
                model_name = "hafidikhsan/wav2vec2-large-xlsr-53-english-pronunciation-evaluation-ep-v2"
                logger.info(f"Loading wav2vec2 pronunciation evaluation model: {model_name}")
                self._wav2vec_processor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
                self._wav2vec_model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
                logger.info("Wav2vec2 pronunciation model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load wav2vec2 model: {e}")
                # Continue without wav2vec2
        return self._wav2vec_model
    
    def analyze_pronunciation(self, 
                            audio_data: bytes, 
                            reference_text: str,
                            sample_rate: int = 16000) -> Dict[str, Any]:
        """Analyze pronunciation offline.
        
        Args:
            audio_data: Raw audio bytes
            reference_text: The text that should be read
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary matching API response format
        """
        try:
            # Save audio to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                # Load audio
                audio, sr = librosa.load(tmp_path, sr=sample_rate)
                
                # 1. Speech Recognition
                recognized_text = self._recognize_speech(audio, sr)
                
                # 2. Get reference phonemes
                reference_phonemes = self._text_to_phonemes(reference_text)
                
                # 3. Get predicted phonemes
                predicted_phonemes = self._audio_to_phonemes(audio, sr)
                
                # 4. Align phonemes
                alignment = self._align_phonemes(reference_phonemes, predicted_phonemes)
                
                # 5. Extract acoustic features
                acoustic_features = self._extract_acoustic_features(audio, sr)
                
                # 6. Calculate scores
                scores = self._calculate_scores(
                    reference_text, 
                    recognized_text,
                    reference_phonemes, 
                    predicted_phonemes,
                    alignment,
                    acoustic_features
                )
                
                # 7. Build response in API format
                response = self._build_response(
                    reference_text,
                    recognized_text,
                    reference_phonemes,
                    predicted_phonemes,
                    alignment,
                    scores
                )
                
                return response
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Error in offline analysis: {e}")
            raise
    
    def _recognize_speech(self, audio: np.ndarray, sr: int) -> str:
        """Recognize speech using Whisper.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Recognized text
        """
        try:
            # Whisper expects audio at 16kHz
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            
            result = self.whisper_model.transcribe(audio, language='en')
            text = result['text'].strip()
            logger.info(f"Recognized text: {text}")
            return text
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
    
    def _text_to_phonemes(self, text: str) -> List[str]:
        """Convert text to phonemes using phonemizer.
        
        Args:
            text: Input text
            
        Returns:
            List of phoneme symbols
        """
        try:
            # Try using eng-to-ipa (simple and works on Windows without dependencies)
            import eng_to_ipa as ipa
            ipa_text = ipa.convert(text)
            # Split IPA into individual symbols (simplified approach)
            # Remove spaces and special characters, keep IPA symbols
            phoneme_list = []
            for char in ipa_text:
                if char not in [' ', '.', ',', '!', '?', '"', "'", '-']:
                    phoneme_list.append(char)
            
            logger.info(f"Reference phonemes (IPA): {phoneme_list[:20]}...")  # Show first 20
            return phoneme_list
        except Exception as e:
            logger.error(f"Text-to-phoneme conversion error: {e}")
            # Ultimate fallback: use character-level
            cleaned = text.replace(' ', '').upper()
            phoneme_list = list(cleaned)
            logger.warning(f"Using character-level fallback: {phoneme_list[:20]}...")
            return phoneme_list
    
    def _audio_to_phonemes(self, audio: np.ndarray, sr: int) -> List[str]:
        """Extract phonemes from audio using wav2vec2.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            List of predicted phoneme symbols
        """
        try:
            if self.wav2vec_model is None:
                # Fallback: use whisper transcription + phonemizer
                text = self._recognize_speech(audio, sr)
                return self._text_to_phonemes(text)
            
            # Resample to 16kHz if needed
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            
            # Process audio with pronunciation evaluation model
            import torch
            # FeatureExtractor expects raw audio array
            inputs = self._wav2vec_processor(
                audio, 
                sampling_rate=16000, 
                return_tensors="pt", 
                padding=True
            )
            
            with torch.no_grad():
                # For SequenceClassification, access logits directly
                outputs = self._wav2vec_model(**inputs)
                logits = outputs.logits
            
            # This model outputs classification scores, not phonemes
            # So we'll use it for pronunciation quality but still use Whisper for phonemes
            logger.info("Using wav2vec2 for pronunciation quality assessment")
            
            # Fallback to Whisper + phonemizer for actual phoneme sequence
            text = self._recognize_speech(audio, sr)
            phoneme_list = self._text_to_phonemes(text)
            
            # Store the quality scores for later use
            self._pronunciation_quality_logits = logits
            
            logger.info(f"Predicted phonemes: {phoneme_list[:20]}...")
            return phoneme_list
            
        except Exception as e:
            logger.error(f"Audio-to-phoneme conversion error: {e}")
            # Fallback: use whisper + text-to-phoneme
            text = self._recognize_speech(audio, sr)
            return self._text_to_phonemes(text)
    
    def _align_phonemes(self, reference: List[str], predicted: List[str]) -> List[Dict[str, Any]]:
        """Align reference and predicted phonemes using Levenshtein distance.
        
        Args:
            reference: Reference phoneme list
            predicted: Predicted phoneme list
            
        Returns:
            Alignment information
        """
        try:
            from Levenshtein import opcodes
            
            # Get alignment operations
            ops = opcodes(reference, predicted)
            
            # Build alignment with scores
            alignment = []
            
            for op, ref_start, ref_end, pred_start, pred_end in ops:
                if op == 'equal':
                    # Correct phonemes
                    for i in range(ref_start, ref_end):
                        alignment.append({
                            'ref_phoneme': reference[i] if i < len(reference) else '',
                            'pred_phoneme': predicted[pred_start + (i - ref_start)] if (pred_start + (i - ref_start)) < len(predicted) else '',
                            'error_type': 'correction',
                            'score': 0.95
                        })
                elif op == 'replace':
                    # Substituted phonemes
                    for i in range(ref_start, ref_end):
                        alignment.append({
                            'ref_phoneme': reference[i] if i < len(reference) else '',
                            'pred_phoneme': predicted[pred_start + (i - ref_start)] if (pred_start + (i - ref_start)) < len(predicted) else '',
                            'error_type': 'substitution',
                            'score': 0.3
                        })
                elif op == 'delete':
                    # Deleted phonemes (present in reference but not in predicted)
                    for i in range(ref_start, ref_end):
                        alignment.append({
                            'ref_phoneme': reference[i] if i < len(reference) else '',
                            'pred_phoneme': '',
                            'error_type': 'deletion',
                            'score': 0.2
                        })
                elif op == 'insert':
                    # Inserted phonemes (present in predicted but not in reference)
                    for i in range(pred_start, pred_end):
                        alignment.append({
                            'ref_phoneme': '',
                            'pred_phoneme': predicted[i] if i < len(predicted) else '',
                            'error_type': 'insertion',
                            'score': 0.4
                        })
            
            logger.info(f"Aligned {len(alignment)} phoneme pairs")
            return alignment
            
        except Exception as e:
            logger.error(f"Phoneme alignment error: {e}")
            # Simple fallback: zip reference and predicted
            alignment = []
            max_len = max(len(reference), len(predicted))
            for i in range(max_len):
                ref_ph = reference[i] if i < len(reference) else ''
                pred_ph = predicted[i] if i < len(predicted) else ''
                is_same = ref_ph == pred_ph and ref_ph != ''
                alignment.append({
                    'ref_phoneme': ref_ph,
                    'pred_phoneme': pred_ph,
                    'error_type': 'correction' if is_same else 'substitution',
                    'score': 0.9 if is_same else 0.5
                })
            return alignment
    
    def _extract_acoustic_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract acoustic features from audio.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Dictionary of acoustic features
        """
        try:
            features = {}
            
            # 1. Pitch (F0) using librosa
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio, 
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr
            )
            features['pitch_mean'] = np.nanmean(f0)
            features['pitch_std'] = np.nanstd(f0)
            features['pitch_range'] = np.nanmax(f0) - np.nanmin(f0)
            
            # 2. Energy/Intensity
            rms = librosa.feature.rms(y=audio)[0]
            features['energy_mean'] = np.mean(rms)
            features['energy_std'] = np.std(rms)
            
            # 3. Speaking rate (syllables per second)
            onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
            features['tempo'] = tempo[0] if len(tempo) > 0 else 0
            
            # 4. Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            features['spectral_centroid_mean'] = np.mean(spectral_centroid)
            
            # 5. Zero crossing rate (correlates with consonant quality)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            features['zcr_mean'] = np.mean(zcr)
            
            # 6. Pauses detection
            intervals = librosa.effects.split(audio, top_db=30)
            features['num_pauses'] = len(intervals) - 1
            features['total_duration'] = len(audio) / sr
            
            logger.info(f"Extracted acoustic features: {list(features.keys())}")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return {}
    
    def _calculate_scores(self, 
                         reference_text: str,
                         recognized_text: str,
                         reference_phonemes: List[str],
                         predicted_phonemes: List[str],
                         alignment: List[Dict[str, Any]],
                         acoustic_features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate pronunciation scores.
        
        Args:
            reference_text: Original text
            recognized_text: Recognized text
            reference_phonemes: Reference phonemes
            predicted_phonemes: Predicted phonemes
            alignment: Phoneme alignment
            acoustic_features: Acoustic features
            
        Returns:
            Dictionary of scores
        """
        scores = {}
        
        # 1. Acoustic score (0-100) based on acoustic features + pronunciation quality model
        acoustic_score = 70.0  # Base score
        
        # If we have pronunciation quality scores from wav2vec2, use them
        if self._pronunciation_quality_logits is not None:
            import torch
            # Get pronunciation quality probability (assuming binary classification: good/bad)
            probs = torch.softmax(self._pronunciation_quality_logits[0], dim=-1)
            # Use the "good pronunciation" probability (typically the higher class)
            quality_score = float(probs.max()) * 100.0
            acoustic_score = (acoustic_score * 0.3) + (quality_score * 0.7)  # Weight model heavily
            logger.info(f"Wav2vec2 pronunciation quality: {quality_score:.2f}/100")
        
        if acoustic_features:
            # Adjust based on pitch stability
            if acoustic_features.get('pitch_std', 0) < 50:
                acoustic_score += 5
            # Adjust based on energy consistency
            if acoustic_features.get('energy_std', 0) < 0.1:
                acoustic_score += 5
            # Cap at 100
            acoustic_score = min(acoustic_score, 100.0)
        scores['acoustic'] = acoustic_score
        
        # 2. Segmental accuracy (1-5) - phoneme-level accuracy
        if len(reference_phonemes) > 0:
            correct_phonemes = sum(1 for a in alignment if a.get('error_type') == 'correction')
            phoneme_accuracy = correct_phonemes / len(reference_phonemes)
            scores['segmental'] = 1.0 + (phoneme_accuracy * 4.0)  # Scale to 1-5
        else:
            scores['segmental'] = 3.0
        
        # 3. Holistic score (1-5) - overall pronunciation quality
        from Levenshtein import ratio
        text_similarity = ratio(reference_text.lower(), recognized_text.lower())
        scores['holistic'] = 1.0 + (text_similarity * 4.0)
        
        # 4. Stress and rhythm (1-5)
        if acoustic_features:
            # Good rhythm = moderate pitch variation
            pitch_std = acoustic_features.get('pitch_std', 0)
            if 20 < pitch_std < 80:
                scores['stress_rhythm'] = 4.0
            elif 10 < pitch_std < 100:
                scores['stress_rhythm'] = 3.5
            else:
                scores['stress_rhythm'] = 3.0
        else:
            scores['stress_rhythm'] = 3.0
        
        # 5. Intonation (1-5)
        if acoustic_features:
            pitch_range = acoustic_features.get('pitch_range', 0)
            # Good intonation = wider pitch range
            if pitch_range > 100:
                scores['intonation'] = 4.0
            elif pitch_range > 50:
                scores['intonation'] = 3.5
            else:
                scores['intonation'] = 3.0
        else:
            scores['intonation'] = 3.0
        
        # 6. Chunking (1-5) - appropriate pausing
        if acoustic_features:
            num_pauses = acoustic_features.get('num_pauses', 0)
            duration = acoustic_features.get('total_duration', 1)
            pause_rate = num_pauses / duration if duration > 0 else 0
            # Appropriate pause rate: 0.5-2 pauses per second
            if 0.5 < pause_rate < 2.0:
                scores['chunking'] = 4.0
            else:
                scores['chunking'] = 3.5
        else:
            scores['chunking'] = 3.5
        
        # 7. Speed and pause (1-5)
        if acoustic_features:
            tempo = acoustic_features.get('tempo', 120)
            # Normal speaking tempo: 100-140 BPM
            if 100 < tempo < 140:
                scores['speed_pause'] = 4.0
            elif 80 < tempo < 160:
                scores['speed_pause'] = 3.5
            else:
                scores['speed_pause'] = 3.0
        else:
            scores['speed_pause'] = 3.5
        
        # Overall reference score (0-1)
        scores['reference_score'] = scores['holistic'] / 5.0
        
        logger.info(f"Calculated scores: {scores}")
        return scores
    
    def _build_response(self,
                       reference_text: str,
                       recognized_text: str,
                       reference_phonemes: List[str],
                       predicted_phonemes: List[str],
                       alignment: List[Dict[str, Any]],
                       scores: Dict[str, float]) -> Dict[str, Any]:
        """Build response in API format.
        
        Args:
            reference_text: Original text
            recognized_text: Recognized text
            reference_phonemes: Reference phonemes
            predicted_phonemes: Predicted phonemes
            alignment: Phoneme alignment
            scores: Calculated scores
            
        Returns:
            Response dictionary matching API format
        """
        # Determine overall comment based on holistic score
        holistic_score = scores.get('holistic', 3.0)
        if holistic_score >= 4.5:
            general_comment = "excellent"
        elif holistic_score >= 4.0:
            general_comment = "good"
        elif holistic_score >= 3.0:
            general_comment = "fair"
        else:
            general_comment = "needs improvement"
        
        # Build word-level analysis
        words = reference_text.split()
        word_detail = []
        for idx, word in enumerate(words):
            # Simple word scoring based on overall accuracy
            word_score = scores.get('holistic', 3.0) / 5.0
            word_detail.append({
                "word": word,
                "score": word_score,
                "word_idx": idx,
                "ph_cnt": len(word),
                "unintelligible": word_score < 0.3,
                "equal_stress": False,
                "stress_error": {}
            })
        
        # Build align_info from alignment
        align_info = []
        phonemes_per_word = len(reference_phonemes) // len(words) if len(words) > 0 else 1
        
        for idx, align in enumerate(alignment):
            word_idx = idx // phonemes_per_word if phonemes_per_word > 0 else 0
            word_idx = min(word_idx, len(words) - 1)
            
            ref_ph = align.get('ref_phoneme', '')
            score_val = align.get('score', 0.9)
            
            align_info.append({
                "word": words[word_idx] if word_idx < len(words) else "",
                "word_idx": word_idx,
                "ref_ph": ref_ph,
                "ref_ph_ipa": [ref_ph],  # Simplified
                "ref_ph_score": score_val,
                "ref_ph_adjusted_score": score_val,
                "phone_error_type": align.get('error_type', 'correction')
            })
        
        # Check for monotonous speech (low pitch variation)
        is_monotonous = scores.get('intonation', 3.0) < 3.0
        
        response = {
            "data": {
                "script_text": reference_text,
                "reference_phoneme": {
                    "phoneme_sequence": " ".join(reference_phonemes),
                    "phoneme_number": len(reference_phonemes)
                },
                "predict_phoneme": {
                    "phoneme_sequence": " ".join(predicted_phonemes),
                    "phoneme_number": len(predicted_phonemes)
                },
                "score_of_refernce": scores.get('reference_score', 0.8),
                "adjusted_sentence_score": scores.get('holistic', 3.0) / 5.0,
                "general_comment": general_comment,
                "stt_recog": recognized_text,
                "align_info": align_info,
                "feedback": {
                    "sentence_detail": {
                        "is_monotonous": is_monotonous,
                        "prosody_of_sentence_end": "normal",
                        "fragmented_speech": scores.get('chunking', 3.5) < 3.0,
                        "awkward_pause": {
                            "flag": scores.get('speed_pause', 3.5) < 3.0,
                            "sentence": ""
                        }
                    },
                    "word_detail": word_detail,
                    "phone_detail": []
                },
                "proficiencyScore": [
                    {"name": "acoustic", "score": scores.get('acoustic', 70.0), "min": 0, "max": 100},
                    {"name": "EN_HOLISTIC", "score": scores.get('holistic', 3.0), "min": 1, "max": 5},
                    {"name": "EN_SEGMENTAL", "score": scores.get('segmental', 3.0), "min": 1, "max": 5},
                    {"name": "EN_CHUNKING", "score": scores.get('chunking', 3.5), "min": 1, "max": 5},
                    {"name": "EN_SPEED_PAUSE", "score": scores.get('speed_pause', 3.5), "min": 1, "max": 5},
                    {"name": "EN_STRESS_RHYTHM", "score": scores.get('stress_rhythm', 3.0), "min": 1, "max": 5},
                    {"name": "EN_INTONATION", "score": scores.get('intonation', 3.0), "min": 1, "max": 5}
                ]
            }
        }
        
        return response


class OfflineAnalyzerError(Exception):
    """Custom exception for offline analyzer errors."""
    pass
