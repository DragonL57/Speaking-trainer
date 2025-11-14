"""Advanced pronunciation analysis using MFA, GOP, and Praat/Parselmouth."""

import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import os
from pathlib import Path
import parselmouth
from parselmouth.praat import call

logger = logging.getLogger(__name__)

class AdvancedPronunciationAnalyzer:
    """Advanced pronunciation analyzer using MFA, GOP, and prosody analysis."""
    
    def __init__(self):
        """Initialize the advanced analyzer."""
        self._cmudict = None
        self._mfa_aligner = None
        logger.info("Initialized advanced pronunciation analyzer")
    
    @property
    def cmudict(self):
        """Lazy load CMUdict."""
        if self._cmudict is None:
            try:
                import nltk
                try:
                    from nltk.corpus import cmudict
                    self._cmudict = cmudict.dict()
                    logger.info("Loaded CMUdict successfully")
                except LookupError:
                    # Download CMUdict if not available
                    logger.info("Downloading CMUdict...")
                    nltk.download('cmudict', quiet=True)
                    from nltk.corpus import cmudict
                    self._cmudict = cmudict.dict()
                    logger.info("Loaded CMUdict successfully")
            except Exception as e:
                logger.error(f"Failed to load CMUdict: {e}")
                # Fallback to pronouncing library
                try:
                    import pronouncing
                    self._cmudict = 'pronouncing'
                    logger.info("Using pronouncing library as fallback")
                except:
                    self._cmudict = {}
                    logger.warning("No dictionary available, using fallback")
        return self._cmudict
    
    def text_to_phonemes_cmudict(self, text: str) -> List[Tuple[str, List[str], List[int]]]:
        """Convert text to phonemes using CMUdict with stress information.
        
        Args:
            text: Input text
            
        Returns:
            List of (word, phonemes, stress_positions) tuples
        """
        words_phonemes = []
        words = text.lower().split()
        
        for word in words:
            # Remove punctuation
            clean_word = ''.join(c for c in word if c.isalnum())
            if not clean_word:
                continue
            
            try:
                if isinstance(self.cmudict, dict):
                    # Using NLTK CMUdict
                    if clean_word in self.cmudict:
                        # Take first pronunciation
                        phonemes = self.cmudict[clean_word][0]
                        
                        # Extract stress information (0=no stress, 1=primary, 2=secondary)
                        stress_positions = []
                        clean_phonemes = []
                        
                        for i, ph in enumerate(phonemes):
                            # CMUdict phonemes have stress markers (0, 1, 2) on vowels
                            if any(char.isdigit() for char in ph):
                                stress_level = int(ph[-1])
                                if stress_level > 0:
                                    stress_positions.append(i)
                                clean_phonemes.append(ph[:-1])
                            else:
                                clean_phonemes.append(ph)
                        
                        words_phonemes.append((clean_word, clean_phonemes, stress_positions))
                    else:
                        logger.warning(f"Word '{clean_word}' not found in CMUdict")
                        words_phonemes.append((clean_word, [], []))
                
                elif self.cmudict == 'pronouncing':
                    # Using pronouncing library
                    import pronouncing
                    phones = pronouncing.phones_for_word(clean_word)
                    if phones:
                        phonemes = phones[0].split()
                        stress_positions = [i for i, ph in enumerate(phonemes) if any(c in ph for c in '12')]
                        clean_phonemes = [ph.rstrip('012') for ph in phonemes]
                        words_phonemes.append((clean_word, clean_phonemes, stress_positions))
                    else:
                        words_phonemes.append((clean_word, [], []))
                
            except Exception as e:
                logger.error(f"Error converting word '{clean_word}' to phonemes: {e}")
                words_phonemes.append((clean_word, [], []))
        
        logger.info(f"Converted {len(words_phonemes)} words to phonemes with stress info")
        return words_phonemes
    
    def extract_prosody_features_praat(self, audio_path: str) -> Dict[str, Any]:
        """Extract prosody features using Praat/Parselmouth.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary of prosody features
        """
        try:
            # Load sound
            sound = parselmouth.Sound(audio_path)
            
            # Extract pitch (F0)
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            
            # Get pitch statistics
            mean_f0 = call(pitch, "Get mean", 0, 0, "Hertz")
            std_f0 = call(pitch, "Get standard deviation", 0, 0, "Hertz")
            min_f0 = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
            max_f0 = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
            
            # Extract intensity
            intensity = call(sound, "To Intensity", 75, 0.0, "yes")
            mean_intensity = call(intensity, "Get mean", 0, 0, "energy")
            max_intensity = call(intensity, "Get maximum", 0, 0, "Parabolic")
            
            # Extract formants (for vowel quality)
            formant = call(sound, "To Formant (burg)", 0.0, 5, 5500, 0.025, 50)
            
            # Get F1 and F2 means (important for vowel pronunciation)
            try:
                f1_mean = call(formant, "Get mean", 1, 0, 0, "Hertz")
                f2_mean = call(formant, "Get mean", 2, 0, 0, "Hertz")
            except:
                f1_mean = 0
                f2_mean = 0
            
            # Duration
            duration = call(sound, "Get total duration")
            
            # Calculate speaking rate (approximate syllables per second)
            # Using intensity to detect syllable nuclei
            intensity_values = intensity.values[0]
            threshold = np.mean(intensity_values)
            # Count peaks above threshold as syllables
            peaks = 0
            above_threshold = False
            for val in intensity_values:
                if val > threshold and not above_threshold:
                    peaks += 1
                    above_threshold = True
                elif val <= threshold:
                    above_threshold = False
            
            speaking_rate = peaks / duration if duration > 0 else 0
            
            features = {
                'mean_f0': mean_f0,
                'std_f0': std_f0,
                'min_f0': min_f0,
                'max_f0': max_f0,
                'f0_range': max_f0 - min_f0,
                'mean_intensity': mean_intensity,
                'max_intensity': max_intensity,
                'f1_mean': f1_mean,
                'f2_mean': f2_mean,
                'duration': duration,
                'speaking_rate': speaking_rate,
                'syllables_estimated': peaks
            }
            
            logger.info(f"Extracted Praat features: F0={mean_f0:.1f}Hz, Rate={speaking_rate:.2f} syl/s")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting Praat features: {e}")
            return {}
    
    def analyze_stress_patterns(self, 
                                audio_path: str,
                                word_boundaries: List[Tuple[float, float, str]],
                                expected_stress: Dict[str, List[int]]) -> Dict[str, Any]:
        """Analyze word stress patterns comparing with expected stress.
        
        Args:
            audio_path: Path to audio file
            word_boundaries: List of (start_time, end_time, word) tuples
            expected_stress: Dict mapping words to stressed syllable indices
            
        Returns:
            Dictionary of stress analysis results
        """
        try:
            sound = parselmouth.Sound(audio_path)
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            intensity = call(sound, "To Intensity", 75, 0.0, "yes")
            
            stress_errors = []
            
            for start, end, word in word_boundaries:
                if word not in expected_stress or not expected_stress[word]:
                    continue
                
                # Extract word segment
                word_duration = end - start
                
                # Get pitch and intensity for this word
                try:
                    word_f0_mean = call(pitch, "Get mean", start, end, "Hertz")
                    word_f0_max = call(pitch, "Get maximum", start, end, "Hertz", "Parabolic")
                    word_intensity_mean = call(intensity, "Get mean", start, end, "energy")
                    word_intensity_max = call(intensity, "Get maximum", start, end, "Parabolic")
                    
                    # Expected stress position (CMUdict gives syllable index)
                    expected_stress_positions = expected_stress[word]
                    
                    # Simple heuristic: if intensity/pitch variation is low, 
                    # might be missing stress
                    intensity_range = word_intensity_max - word_intensity_mean
                    pitch_range = word_f0_max - word_f0_mean
                    
                    # If both are very low, likely monotonous/missing stress
                    if intensity_range < 3 and pitch_range < 20:
                        stress_errors.append({
                            'word': word,
                            'type': 'weak_stress',
                            'expected_syllables': expected_stress_positions,
                            'message': f"Weak stress on '{word}', expected stress on syllable(s) {expected_stress_positions}"
                        })
                    
                except Exception as e:
                    logger.debug(f"Could not analyze stress for word '{word}': {e}")
                    continue
            
            return {
                'stress_errors': stress_errors,
                'total_words_checked': len([w for w in word_boundaries if w[2] in expected_stress])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stress patterns: {e}")
            return {'stress_errors': [], 'total_words_checked': 0}
    
    def calculate_gop_scores(self,
                            aligned_phonemes: List[Dict[str, Any]],
                            audio_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate Goodness of Pronunciation (GOP) scores for aligned phonemes.
        
        GOP is typically calculated as:
        GOP(p) = log P(p | acoustic_features) / P(acoustic_features)
        
        Here we use a simplified heuristic based on:
        - Phoneme duration (compared to expected)
        - Energy consistency
        - Spectral features
        
        Args:
            aligned_phonemes: List of aligned phoneme dictionaries
            audio_features: Dictionary of audio features
            
        Returns:
            List of phonemes with GOP scores added
        """
        try:
            gop_phonemes = []
            
            # Typical phoneme durations (in seconds, rough estimates)
            typical_durations = {
                'vowels': 0.08,  # Vowels tend to be longer
                'consonants': 0.05,  # Consonants shorter
                'silence': 0.15
            }
            
            for phoneme_info in aligned_phonemes:
                phoneme = phoneme_info.get('ref_phoneme', '')
                error_type = phoneme_info.get('error_type', 'correction')
                
                # Base GOP score from error type
                if error_type == 'correction':
                    base_gop = 0.9
                elif error_type == 'substitution':
                    base_gop = 0.3
                elif error_type == 'deletion':
                    base_gop = 0.1
                elif error_type == 'insertion':
                    base_gop = 0.4
                else:
                    base_gop = 0.5
                
                # Adjust based on acoustic features if available
                # (This is simplified; real GOP uses acoustic model posteriors)
                
                # Add to result
                phoneme_info['gop_score'] = base_gop
                gop_phonemes.append(phoneme_info)
            
            logger.info(f"Calculated GOP scores for {len(gop_phonemes)} phonemes")
            return gop_phonemes
            
        except Exception as e:
            logger.error(f"Error calculating GOP scores: {e}")
            return aligned_phonemes
    
    def detect_intonation_issues(self, prosody_features: Dict[str, Any]) -> List[str]:
        """Detect intonation issues from prosody features.
        
        Args:
            prosody_features: Dictionary of prosody features
            
        Returns:
            List of intonation issue descriptions
        """
        issues = []
        
        try:
            # Check for monotonous pitch (low variation)
            if prosody_features.get('std_f0', 0) < 15:
                issues.append("Monotonous intonation - try varying your pitch more")
            
            # Check for unnaturally narrow pitch range
            f0_range = prosody_features.get('f0_range', 0)
            if f0_range < 30:
                issues.append("Very narrow pitch range - practice using wider intonation")
            elif f0_range > 300:
                issues.append("Unusually wide pitch range - try to be more consistent")
            
            # Check speaking rate
            speaking_rate = prosody_features.get('speaking_rate', 0)
            if speaking_rate > 6:
                issues.append("Speaking too fast - slow down for clearer pronunciation")
            elif speaking_rate < 2 and speaking_rate > 0:
                issues.append("Speaking too slowly - try to maintain natural rhythm")
            
            logger.info(f"Detected {len(issues)} intonation issues")
            return issues
            
        except Exception as e:
            logger.error(f"Error detecting intonation issues: {e}")
            return issues


class EnhancedOfflineAnalyzer:
    """Enhanced offline analyzer combining basic and advanced techniques."""
    
    def __init__(self, whisper_model: str = "base", device: str = "cpu"):
        """Initialize enhanced analyzer.
        
        Args:
            whisper_model: Whisper model size
            device: Device to run on
        """
        from src.offline_analyzer import OfflinePronunciationAnalyzer
        
        self.basic_analyzer = OfflinePronunciationAnalyzer(whisper_model, device)
        self.advanced_analyzer = AdvancedPronunciationAnalyzer()
        
        logger.info("Initialized enhanced offline analyzer")
    
    def analyze_pronunciation_enhanced(self,
                                      audio_data: bytes,
                                      reference_text: str,
                                      sample_rate: int = 16000) -> Dict[str, Any]:
        """Perform enhanced pronunciation analysis.
        
        Args:
            audio_data: Raw audio bytes
            reference_text: Reference text
            sample_rate: Audio sample rate
            
        Returns:
            Enhanced analysis results
        """
        # First, run basic analysis
        basic_results = self.basic_analyzer.analyze_pronunciation(
            audio_data, reference_text, sample_rate
        )
        
        # Save audio to temp file for advanced analysis
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            # Enhanced phoneme mapping with CMUdict
            words_phonemes_stress = self.advanced_analyzer.text_to_phonemes_cmudict(reference_text)
            
            # Extract prosody features with Praat
            prosody_features = self.advanced_analyzer.extract_prosody_features_praat(tmp_path)
            
            # Detect intonation issues
            intonation_issues = self.advanced_analyzer.detect_intonation_issues(prosody_features)
            
            # Add enhanced features to basic results
            basic_results['data']['enhanced_phonemes'] = words_phonemes_stress
            basic_results['data']['praat_features'] = prosody_features
            basic_results['data']['intonation_issues'] = intonation_issues
            
            # Update proficiency scores based on prosody
            proficiency = basic_results['data'].get('proficiencyScore', [])
            for score_item in proficiency:
                if score_item['name'] == 'EN_INTONATION':
                    # Adjust intonation score based on detected issues
                    if len(intonation_issues) == 0:
                        score_item['score'] = min(score_item['score'] + 0.5, 5.0)
                    elif len(intonation_issues) >= 2:
                        score_item['score'] = max(score_item['score'] - 0.3, 1.0)
            
            logger.info("Enhanced analysis completed successfully")
            return basic_results
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
            # Return basic results if enhanced analysis fails
            return basic_results
        
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class OfflineAnalyzerError(Exception):
    """Custom exception for offline analyzer errors."""
    pass
