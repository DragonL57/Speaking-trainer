"""
Unified offline pronunciation analyzer combining:
- Whisper ASR (OpenAI/Hugging Face)
- Acoustic features (librosa)
- CMUdict G2P with stress markers
- Praat prosody analysis
- GOP scoring and stress pattern detection
"""

import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import os
from pathlib import Path
import nltk
import pronouncing

# Lazy imports for heavy libraries
import warnings
warnings.filterwarnings('ignore')

# Check Praat availability
try:
    import parselmouth
    from parselmouth.praat import call
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    parselmouth = None

logger = logging.getLogger(__name__)

class OfflinePronunciationAnalyzer:
    """
    Unified offline pronunciation analyzer with advanced features.
    Combines Whisper ASR, acoustic analysis, CMUdict, Praat prosody, and GOP scoring.
    """
    
    def __init__(self, whisper_model: str = "base", device: str = "cpu"):
        """Initialize the offline analyzer.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            device: Device to run models on (cpu, cuda)
        """
        self.whisper_model_name = whisper_model
        self.device = device
        self._whisper_model = None
        self._whisper_processor = None  # For Hugging Face models
        self._phonemizer = None
        
        logger.info(f"Initialized offline analyzer with Whisper model: {whisper_model}")
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            try:
                # Check if model name is from Hugging Face (contains /)
                if '/' in self.whisper_model_name:
                    # Load from Hugging Face transformers
                    from transformers import WhisperProcessor, WhisperForConditionalGeneration
                    logger.info(f"Loading Whisper model from Hugging Face: {self.whisper_model_name}")
                    self._whisper_processor = WhisperProcessor.from_pretrained(self.whisper_model_name)
                    self._whisper_model = WhisperForConditionalGeneration.from_pretrained(self.whisper_model_name)
                    self._whisper_model.to(self.device)
                    logger.info("Hugging Face Whisper model loaded successfully")
                else:
                    # Load from OpenAI whisper
                    import whisper
                    logger.info(f"Loading OpenAI Whisper model: {self.whisper_model_name}")
                    self._whisper_model = whisper.load_model(self.whisper_model_name, device=self.device)
                    self._whisper_processor = None
                    logger.info("OpenAI Whisper model loaded successfully")
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
    def cmudict(self):
        """Lazy load CMUdict."""
        if not hasattr(self, '_cmudict'):
            try:
                self._cmudict = nltk.corpus.cmudict.dict()
                logger.info(f"CMUdict loaded with {len(self._cmudict)} entries")
            except LookupError:
                logger.info("Downloading CMUdict...")
                nltk.download('cmudict', quiet=True)
                self._cmudict = nltk.corpus.cmudict.dict()
            except Exception as e:
                logger.warning(f"Failed to load CMUdict: {e}. Using pronouncing fallback.")
                self._cmudict = None
        return self._cmudict
    
    def text_to_phonemes_cmudict(self, text: str) -> List[Tuple[str, List[str], List[int]]]:
        """
        Convert text to phonemes using CMUdict with stress markers.
        
        Returns:
            List of (word, phonemes, stress_positions) tuples
            Example: [("hello", ["HH", "AH0", "L", "OW1"], [3])]
        """
        words = text.lower().split()
        result = []
        
        for word in words:
            # Clean word of punctuation
            clean_word = ''.join(c for c in word if c.isalnum() or c == "'")
            if not clean_word:
                continue
            
            phonemes = None
            stress_positions = []
            
            # Try CMUdict first
            if self.cmudict and clean_word in self.cmudict:
                # CMUdict returns list of pronunciations, take first
                phonemes = self.cmudict[clean_word][0]
                # Extract stress positions
                for i, p in enumerate(phonemes):
                    if p[-1].isdigit():
                        stress_level = int(p[-1])
                        if stress_level > 0:  # 1 = primary, 2 = secondary
                            stress_positions.append(i)
            else:
                # Fallback to pronouncing library
                try:
                    phones = pronouncing.phones_for_word(clean_word)
                    if phones:
                        phonemes = phones[0].split()
                        for i, p in enumerate(phonemes):
                            if p[-1].isdigit() and int(p[-1]) > 0:
                                stress_positions.append(i)
                except Exception as e:
                    logger.debug(f"Pronouncing failed for '{clean_word}': {e}")
            
            # If still no phonemes, use basic IPA converter
            if phonemes is None:
                try:
                    import eng_to_ipa as ipa
                    phonemes = list(ipa.convert(clean_word))
                except:
                    phonemes = list(clean_word)
            
            result.append((clean_word, phonemes, stress_positions))
        
        return result
    
    def extract_prosody_features_praat(self, audio_path: str, sr: int = 16000) -> Dict[str, Any]:
        """
        Extract prosody features using Praat/Parselmouth.
        
        Returns:
            Dictionary with: f0_mean, f0_std, f0_range, intensity_mean, 
            formants (F1, F2), duration, syllable_rate
        """
        if not PARSELMOUTH_AVAILABLE:
            logger.warning("Parselmouth not available, skipping Praat features")
            return {}
        
        try:
            sound = parselmouth.Sound(audio_path)
            
            # Pitch (F0) analysis
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            f0_values = pitch.selected_array['frequency']
            f0_values = f0_values[f0_values > 0]  # Remove unvoiced frames
            
            # Intensity analysis
            intensity = call(sound, "To Intensity", 75, 0.0, True)
            # Get intensity values using get_value method instead of List values
            duration = sound.get_total_duration()
            num_frames = int(duration * 100)  # Sample at 100 Hz
            intensity_values = []
            for i in range(num_frames):
                t = i * 0.01
                val = call(intensity, "Get value at time", t, "Cubic")
                if not np.isnan(val):
                    intensity_values.append(val)
            intensity_values = np.array(intensity_values)
            
            # Formant analysis
            formant = call(sound, "To Formant (burg)", 0.0, 5, 5500, 0.025, 50)
            
            # Extract F1 and F2 at midpoint
            midpoint = duration / 2
            f1 = call(formant, "Get value at time", 1, midpoint, "Hertz", "Linear")
            f2 = call(formant, "Get value at time", 2, midpoint, "Hertz", "Linear")
            
            # Syllable nuclei detection (approximation)
            intensity_threshold = np.mean(intensity_values) - np.std(intensity_values)
            syllable_count = 0
            in_syllable = False
            for val in intensity_values:
                if val > intensity_threshold and not in_syllable:
                    syllable_count += 1
                    in_syllable = True
                elif val <= intensity_threshold:
                    in_syllable = False
            
            syllable_rate = syllable_count / duration if duration > 0 else 0
            
            return {
                'f0_mean': float(np.mean(f0_values)) if len(f0_values) > 0 else 0,
                'f0_std': float(np.std(f0_values)) if len(f0_values) > 0 else 0,
                'f0_range': float(np.ptp(f0_values)) if len(f0_values) > 0 else 0,
                'intensity_mean': float(np.mean(intensity_values)) if len(intensity_values) > 0 else 0,
                'f1': float(f1) if not np.isnan(f1) else 0,
                'f2': float(f2) if not np.isnan(f2) else 0,
                'duration': float(duration),
                'syllable_rate': float(syllable_rate)
            }
        except Exception as e:
            logger.error(f"Praat feature extraction failed: {e}")
            return {}
    
    def analyze_stress_patterns(self, 
                                expected_phonemes: List[Tuple[str, List[str], List[int]]],
                                prosody_features: Dict[str, Any]) -> List[str]:
        """
        Analyze stress patterns by comparing expected vs actual.
        
        Returns:
            List of stress-related issues
        """
        issues = []
        
        # Check if any words have expected stress
        words_with_stress = [w for w in expected_phonemes if w[2]]  # w[2] = stress_positions
        
        if not words_with_stress:
            return issues
        
        # Analyze based on prosody features
        f0_std = prosody_features.get('f0_std', 0)
        f0_range = prosody_features.get('f0_range', 0)
        
        # Weak stress indicators
        if f0_std < 10:
            issues.append("Very flat pitch - insufficient stress variation")
        elif f0_std < 20:
            issues.append("Limited pitch variation - weak stress patterns")
        
        if f0_range < 30:
            issues.append("Narrow pitch range - stress not clearly marked")
        
        return issues
    
    def calculate_gop_scores(self, align_info: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate simplified GOP (Goodness of Pronunciation) scores.
        
        Returns:
            List of scores (0-1) for each aligned segment
        """
        scores = []
        
        for segment in align_info:
            error_type = segment.get('error_type', 'correct')
            
            # Simplified GOP based on error type
            if error_type == 'correct':
                score = 1.0
            elif error_type == 'correction':
                score = 0.9  # Minor deviation
            elif error_type == 'substitution':
                score = 0.3  # Wrong phoneme
            elif error_type == 'insertion':
                score = 0.5  # Extra phoneme
            elif error_type == 'deletion':
                score = 0.2  # Missing phoneme
            else:
                score = 0.7  # Unknown
            
            scores.append(score)
        
        return scores
    
    def detect_intonation_issues(self, prosody_features: Dict[str, Any]) -> List[str]:
        """
        Detect intonation issues based on prosody features.
        
        Returns:
            List of detected issues
        """
        issues = []
        
        f0_mean = prosody_features.get('f0_mean', 0)
        f0_std = prosody_features.get('f0_std', 0)
        f0_range = prosody_features.get('f0_range', 0)
        syllable_rate = prosody_features.get('syllable_rate', 0)
        
        # Monotonous speech
        if f0_std < 15:
            issues.append("Monotonous speech - very little pitch variation")
        
        # Narrow pitch range
        if f0_range < 30:
            issues.append("Very narrow pitch range - lacks expressiveness")
        
        # Speaking rate issues
        if syllable_rate > 6:
            issues.append("Speaking too fast - may affect clarity")
        elif syllable_rate < 2:
            issues.append("Speaking too slowly - lacks fluency")
        
        return issues
    
    def analyze_pronunciation(self, 
                            audio_data: bytes, 
                            reference_text: str,
                            sample_rate: int = 16000,
                            use_advanced: bool = True) -> Dict[str, Any]:
        """
        Analyze pronunciation with optional advanced features.
        
        Args:
            audio_data: Raw audio bytes
            reference_text: The text that should be read
            sample_rate: Audio sample rate
            use_advanced: Whether to use advanced features (CMUdict, Praat, GOP)
            
        Returns:
            Dictionary matching API response format with advanced features
        """
        try:
            # Save audio to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                # Load audio
                audio, sr = librosa.load(tmp_path, sr=sample_rate)
                
                # Ensure Whisper model is loaded first
                _ = self.whisper_model
                
                # 1. Speech Recognition
                recognized_text = self._recognize_speech(audio, sr)
                
                # 2. Get reference phonemes (basic IPA)
                reference_phonemes = self._text_to_phonemes(reference_text)
                
                # 3. Get predicted phonemes
                predicted_phonemes = self._audio_to_phonemes(audio, sr)
                
                # 4. Align phonemes
                alignment = self._align_phonemes(reference_phonemes, predicted_phonemes)
                
                # 5. Extract acoustic features
                acoustic_features = self._extract_acoustic_features(audio, sr)
                
                # 6. Advanced features (if enabled)
                advanced_data = {}
                if use_advanced:
                    # CMUdict phonemes with stress
                    cmudict_phonemes = self.text_to_phonemes_cmudict(reference_text)
                    advanced_data['cmudict_phonemes'] = cmudict_phonemes
                    
                    # Praat prosody features
                    prosody_features = self.extract_prosody_features_praat(tmp_path, sr)
                    advanced_data['prosody_features'] = prosody_features
                    
                    # GOP scores
                    gop_scores = self.calculate_gop_scores(alignment)
                    advanced_data['gop_scores'] = gop_scores
                    
                    # Stress analysis
                    stress_issues = self.analyze_stress_patterns(cmudict_phonemes, prosody_features)
                    advanced_data['stress_issues'] = stress_issues
                    
                    # Intonation analysis
                    intonation_issues = self.detect_intonation_issues(prosody_features)
                    advanced_data['intonation_issues'] = intonation_issues
                    
                    logger.info(f"Advanced analysis: {len(cmudict_phonemes)} words with stress info, "
                              f"{len(stress_issues)} stress issues, {len(intonation_issues)} intonation issues")
                
                # 7. Calculate scores (with advanced data if available)
                scores = self._calculate_scores(
                    reference_text, 
                    recognized_text,
                    reference_phonemes, 
                    predicted_phonemes,
                    alignment,
                    acoustic_features,
                    advanced_data
                )
                
                # 8. Build response in API format
                response = self._build_response(
                    reference_text,
                    recognized_text,
                    reference_phonemes,
                    predicted_phonemes,
                    alignment,
                    scores,
                    advanced_data
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
            
            # Ensure model is loaded
            model = self.whisper_model
            
            # Check if using Hugging Face or OpenAI model
            if self._whisper_processor is not None:
                # Hugging Face transformers model
                import torch
                
                # Process audio input
                inputs = self._whisper_processor(audio, sampling_rate=16000, return_tensors="pt")
                
                # Move to device
                input_features = inputs.input_features.to(self.device)
                
                # Generate transcription
                # Most fine-tuned Whisper models are English-only
                # Don't specify language/task to avoid errors
                with torch.no_grad():
                    generated_ids = model.generate(input_features)
                
                # Decode output
                text = self._whisper_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                text = text.strip()
            else:
                # OpenAI whisper model
                result = model.transcribe(audio, language='en')
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
        """Extract phonemes from audio using Whisper transcription.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            List of predicted phoneme symbols
        """
        try:
            # Use Whisper for transcription, then convert to phonemes
            text = self._recognize_speech(audio, sr)
            phoneme_list = self._text_to_phonemes(text)
            
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
                         acoustic_features: Dict[str, Any],
                         advanced_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Calculate pronunciation scores with optional advanced features.
        
        Args:
            reference_text: Original text
            recognized_text: Recognized text
            reference_phonemes: Reference phonemes
            predicted_phonemes: Predicted phonemes
            alignment: Phoneme alignment
            acoustic_features: Acoustic features
            advanced_data: Optional advanced analysis data (GOP, stress, intonation)
            
        Returns:
            Dictionary of scores
        """
        scores = {}
        advanced_data = advanced_data or {}
        
        # 1. Acoustic score (0-100) based on acoustic features
        acoustic_score = 70.0  # Base score
        
        if acoustic_features:
            # Adjust based on pitch stability
            if acoustic_features.get('pitch_std', 0) < 50:
                acoustic_score += 10
            # Adjust based on energy consistency
            if acoustic_features.get('energy_std', 0) < 0.1:
                acoustic_score += 10
            # Cap at 100
            acoustic_score = min(acoustic_score, 100.0)
        
        # Use GOP scores if available
        gop_scores = advanced_data.get('gop_scores', [])
        if gop_scores:
            avg_gop = np.mean(gop_scores)
            acoustic_score = avg_gop * 100  # GOP is 0-1, scale to 0-100
        
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
        
        # Penalize stress issues if available
        stress_issues = advanced_data.get('stress_issues', [])
        if stress_issues:
            scores['stress_rhythm'] = max(1.0, scores['stress_rhythm'] - len(stress_issues) * 0.3)
        
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
        
        # Penalize intonation issues if available
        intonation_issues = advanced_data.get('intonation_issues', [])
        if intonation_issues:
            scores['intonation'] = max(1.0, scores['intonation'] - len(intonation_issues) * 0.3)
        
        # Use prosody features if available
        prosody_features = advanced_data.get('prosody_features', {})
        if prosody_features:
            syllable_rate = prosody_features.get('syllable_rate', 0)
            # Optimal syllable rate: 3-5 syllables/second
            if 3 <= syllable_rate <= 5:
                scores['speed_pause'] = 4.5
            elif 2 <= syllable_rate <= 6:
                scores['speed_pause'] = 3.5
            else:
                scores['speed_pause'] = 2.5
        
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
        if 'speed_pause' not in scores:  # If not already set by prosody
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
                       scores: Dict[str, float],
                       advanced_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build response in API format with optional advanced data.
        
        
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
        advanced_data = advanced_data or {}
        
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
        
        # Add advanced feedback
        stress_issues = advanced_data.get('stress_issues', [])
        intonation_issues = advanced_data.get('intonation_issues', [])
        if stress_issues:
            general_comment += f" ({len(stress_issues)} stress issue(s))"
        if intonation_issues:
            general_comment += f" ({len(intonation_issues)} intonation issue(s))"
        
        # Build word-level analysis
        words = reference_text.split()
        word_detail = []
        cmudict_phonemes = advanced_data.get('cmudict_phonemes', [])
        
        for idx, word in enumerate(words):
            # Simple word scoring based on overall accuracy
            word_score = scores.get('holistic', 3.0) / 5.0
            
            # Get stress info from CMUdict if available
            stress_error = {}
            if idx < len(cmudict_phonemes):
                _, phonemes, stress_positions = cmudict_phonemes[idx]
                if stress_positions:
                    stress_error = {
                        "expected_stress": stress_positions,
                        "has_stress": len(stress_positions) > 0
                    }
            
            word_detail.append({
                "word": word,
                "score": word_score,
                "word_idx": idx,
                "ph_cnt": len(word),
                "unintelligible": word_score < 0.3,
                "equal_stress": False,
                "stress_error": stress_error
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
        
        # Build sentence detail with advanced features
        sentence_detail = {
            "is_monotonous": is_monotonous,
            "prosody_of_sentence_end": "normal",
            "fragmented_speech": scores.get('chunking', 3.5) < 3.0,
            "awkward_pause": {
                "flag": scores.get('speed_pause', 3.5) < 3.0,
                "sentence": ""
            }
        }
        
        # Add advanced issues
        if stress_issues:
            sentence_detail["stress_issues"] = stress_issues
        if intonation_issues:
            sentence_detail["intonation_issues"] = intonation_issues
        
        # Add prosody features if available
        prosody_features = advanced_data.get('prosody_features', {})
        if prosody_features:
            sentence_detail["prosody_features"] = {
                "f0_mean": prosody_features.get('f0_mean', 0),
                "f0_std": prosody_features.get('f0_std', 0),
                "f0_range": prosody_features.get('f0_range', 0),
                "syllable_rate": prosody_features.get('syllable_rate', 0)
            }
        
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
                    "sentence_detail": sentence_detail,
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
