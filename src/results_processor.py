"""Process and format API response data for display."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from config.constants import (
    SCORE_THRESHOLDS,
    SCORE_COLORS,
    PROSODY_STATUS,
    SCORE_SCALES
)

logger = logging.getLogger(__name__)

@dataclass
class ProficiencyScores:
    """Container for proficiency scores."""
    acoustic_score: float = 0.0
    holistic_score: float = 0.0
    segmental_accuracy: float = 0.0
    chunking: float = 0.0
    speed_and_pause: float = 0.0
    stress_and_rhythm: float = 0.0
    intonation: float = 0.0

@dataclass
class ProsodyAnalysis:
    """Container for prosody analysis results."""
    intonation_status: str = ""
    sentence_ending: str = ""
    speech_flow: str = ""
    pauses: str = ""
    pause_sentence: str = ""  # To show where [pause] occurred

@dataclass
class PhonemeDetail:
    """Container for individual phoneme details."""
    phoneme: str  # Phoneme symbol (e.g., "W", "IY")
    ipa: str  # IPA symbol (e.g., "w", "i")
    score: float  # Score for this phoneme
    error_type: str  # Error type (correction, substitution, etc.)

@dataclass
class WordAnalysis:
    """Container for word-level analysis."""
    word: str
    score: float
    word_idx: int
    phoneme_count: int
    ipa: str = ""  # IPA transcription for the word
    phoneme_details: List[PhonemeDetail] = field(default_factory=list)  # Detailed phoneme info
    is_unintelligible: bool = False
    has_equal_stress: bool = False
    stress_error_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PhonemeError:
    """Container for phoneme-level error information."""
    word: str
    word_idx: int
    error_type: str
    error_tag: str
    definition: str
    spell_view: str

@dataclass
class ProcessedResults:
    """Container for all processed results."""
    overall_comment: str = ""
    recognized_text: str = ""
    reference_score: float = 0.0
    proficiency_scores: ProficiencyScores = field(default_factory=ProficiencyScores)
    prosody_analysis: ProsodyAnalysis = field(default_factory=ProsodyAnalysis)
    word_analyses: List[WordAnalysis] = field(default_factory=list)
    phoneme_errors: List[PhonemeError] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)

class ResultsProcessor:
    """Process pronunciation API responses into structured data."""
    
    def process_api_response(self, response: Dict[str, Any]) -> ProcessedResults:
        """Process raw API response into structured results.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            ProcessedResults object with all extracted data
        """
        try:
            results = ProcessedResults(raw_response=response)
            
            # Extract main data section
            data = response.get("data", {})
            
            # Process overall results
            results.overall_comment = data.get("general_comment", "")
            results.recognized_text = data.get("stt_recog", "")
            results.reference_score = self._safe_float(data.get("score_of_refernce", 0)) * 100  # Convert to percentage
            
            # Process proficiency scores from proficiencyScore field
            proficiency_scores = data.get("proficiencyScore", [])
            results.proficiency_scores = self._extract_proficiency_scores(proficiency_scores)
            
            # Process feedback data
            feedback = data.get("feedback", {})
            
            # Process prosody analysis from feedback
            sentence_detail = feedback.get("sentence_detail", {}) if isinstance(feedback, dict) else {}
            results.prosody_analysis = self._extract_prosody_analysis(sentence_detail)
            
            # Process word-level analysis from word_detail in feedback
            word_detail = feedback.get("word_detail", []) if isinstance(feedback, dict) else []
            results.word_analyses = self._extract_word_analyses_from_detail(word_detail)
            
            # Extract and merge IPA data from align_info
            align_info = data.get("align_info", [])
            self._merge_ipa_to_word_analyses(results.word_analyses, align_info)
            
            # Process phoneme errors from feedback
            results.phoneme_errors = self._extract_phoneme_errors(feedback)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing API response: {e}")
            # Return partial results rather than failing completely
            return ProcessedResults(
                overall_comment="Error processing results",
                raw_response=response
            )
    
    def _extract_proficiency_scores(self, proficiency_scores: List[Dict[str, Any]]) -> ProficiencyScores:
        """Extract proficiency scores from proficiency data.
        
        Args:
            proficiency_scores: proficiencyScore array from API response
            
        Returns:
            ProficiencyScores object
        """
        scores = ProficiencyScores()
        
        # Extract scores from the list based on 'name' field
        for score_item in proficiency_scores:
            name = score_item.get("name", "")
            score_value = self._safe_float(score_item.get("score", 0))
            
            # Skip acoustic score as requested
            if name == "acoustic":
                scores.acoustic_score = score_value
            elif name == "EN_HOLISTIC":
                scores.holistic_score = score_value
            elif name == "EN_SEGMENTAL":
                scores.segmental_accuracy = score_value
            elif name == "EN_CHUNKING":
                scores.chunking = score_value
            elif name == "EN_SPEED_PAUSE":
                scores.speed_and_pause = score_value
            elif name == "EN_STRESS_RHYTHM":
                scores.stress_and_rhythm = score_value
            elif name == "EN_INTONATION":
                scores.intonation = score_value
        
        return scores
    
    def _extract_prosody_analysis(self, sentence_detail: Dict[str, Any]) -> ProsodyAnalysis:
        """Extract prosody analysis from sentence_detail.
        
        Args:
            sentence_detail: sentence_detail from feedback in API response
            
        Returns:
            ProsodyAnalysis object with awkward_pause info
        """
        # Extract prosody indicators
        is_monotonous = sentence_detail.get("is_monotonous", False)
        prosody_of_sentence_end = sentence_detail.get("prosody_of_sentence_end", "normal")
        
        # Extract awkward pause info using the flag field
        awkward_pause = sentence_detail.get("awkward_pause", {})
        has_awkward_pause = awkward_pause.get("flag", False)
        pause_sentence = awkward_pause.get("sentence", "")
        
        # Map sentence ending to our status
        sentence_ending_status = "Normal"
        if prosody_of_sentence_end == "awkward_rising":
            sentence_ending_status = "Rising"
        elif prosody_of_sentence_end == "awkward_falling":
            sentence_ending_status = "Falling"
        
        # Create prosody analysis with pause info
        analysis = ProsodyAnalysis(
            intonation_status=PROSODY_STATUS["intonation"]["poor" if is_monotonous else "good"],
            sentence_ending=sentence_ending_status,
            speech_flow=PROSODY_STATUS["speech_flow"]["good"],  # Not directly provided
            pauses="Awkward" if has_awkward_pause else "Natural"
        )
        
        # Store the pause sentence for display if needed
        analysis.pause_sentence = pause_sentence if has_awkward_pause else ""
        
        return analysis
    
    def _get_sentence_ending_status(self, sentence_detail: Dict[str, Any]) -> str:
        """Determine sentence ending status.
        
        Args:
            sentence_detail: Sentence detail data
            
        Returns:
            Sentence ending status string
        """
        if sentence_detail.get("sentence_ending_is_normal", True):
            return PROSODY_STATUS["sentence_ending"]["normal"]
        elif sentence_detail.get("sentence_ending_is_rising", False):
            return PROSODY_STATUS["sentence_ending"]["rising"]
        else:
            return PROSODY_STATUS["sentence_ending"]["falling"]
    
    def _extract_word_analyses(self, feedback: Dict[str, Any]) -> List[WordAnalysis]:
        """Extract word-level analysis data.
        
        Args:
            feedback: Feedback section of API response
            
        Returns:
            List of WordAnalysis objects
        """
        word_analyses = []
        
        # Get word scores
        word_scores = feedback.get("word_score", [])
        align_info = feedback.get("align_info", [])
        
        # Group align_info by word_idx to get IPA for each word
        word_ipa_map = {}
        for align_item in align_info:
            word_idx = align_item.get("word_idx", 0)
            ref_ph_ipa = align_item.get("ref_ph_ipa", [])
            if ref_ph_ipa:
                ipa_symbol = ref_ph_ipa[0] if isinstance(ref_ph_ipa, list) else ref_ph_ipa
                if word_idx not in word_ipa_map:
                    word_ipa_map[word_idx] = []
                word_ipa_map[word_idx].append(ipa_symbol)
        
        # Create word analysis for each word
        for i, word_data in enumerate(word_scores):
            word = word_data.get("word", "")
            score = self._safe_float(word_data.get("score", 0))
            word_idx = word_data.get("word_idx", i)
            
            # Get IPA for this word
            ipa = " ".join(word_ipa_map.get(word_idx, []))
            
            # Get additional info from align_info if available
            phoneme_count = len(word_ipa_map.get(word_idx, []))
            is_unintelligible = False
            has_equal_stress = False
            stress_errors = []
            
            # Note: Additional phoneme-level checks would require more processing
            
            word_analyses.append(WordAnalysis(
                word=word,
                score=score,
                word_idx=word_idx,
                phoneme_count=phoneme_count,
                ipa=ipa,
                is_unintelligible=is_unintelligible,
                has_equal_stress=has_equal_stress,
                stress_error_info={}
            ))
        
        return word_analyses
    
    def _merge_ipa_to_word_analyses(self, word_analyses: List[WordAnalysis], align_info: List[Dict[str, Any]]) -> None:
        """Merge IPA data from align_info into word_analyses.
        
        Args:
            word_analyses: List of WordAnalysis objects to update
            align_info: align_info array from API response
        """
        # Group align_info by word_idx to get IPA and phoneme details for each word
        word_data_map = {}
        for align_item in align_info:
            word_idx = align_item.get("word_idx", 0)
            ref_ph_ipa = align_item.get("ref_ph_ipa", [])
            ref_ph = align_item.get("ref_ph", "")
            ref_ph_score = self._safe_float(align_item.get("ref_ph_adjusted_score", align_item.get("ref_ph_score", 1.0)))
            error_type = align_item.get("phone_error_type", "correction")
            
            if word_idx not in word_data_map:
                word_data_map[word_idx] = {
                    "ipa_symbols": [],
                    "phoneme_details": []
                }
            
            if ref_ph_ipa:
                ipa_symbol = ref_ph_ipa[0] if isinstance(ref_ph_ipa, list) else ref_ph_ipa
                word_data_map[word_idx]["ipa_symbols"].append(ipa_symbol)
                
                # Create phoneme detail
                phoneme_detail = PhonemeDetail(
                    phoneme=ref_ph,
                    ipa=ipa_symbol,
                    score=ref_ph_score * 100,  # Convert to percentage
                    error_type=error_type
                )
                word_data_map[word_idx]["phoneme_details"].append(phoneme_detail)
        
        # Update each word_analysis with its IPA and phoneme details
        for word_analysis in word_analyses:
            word_idx = word_analysis.word_idx
            if word_idx in word_data_map:
                word_data = word_data_map[word_idx]
                word_analysis.ipa = " ".join(word_data["ipa_symbols"])
                word_analysis.phoneme_details = word_data["phoneme_details"]
    
    def _extract_word_analyses_from_detail(self, word_detail: List[Dict[str, Any]]) -> List[WordAnalysis]:
        """Extract word-level analysis from word_detail data.
        
        Args:
            word_detail: word_detail array from feedback in API response
            
        Returns:
            List of WordAnalysis objects
        """
        word_analyses = []
        
        for word_data in word_detail:
            word = word_data.get("word", "")
            score = self._safe_float(word_data.get("score", 0))
            word_idx = word_data.get("word_idx", 0)
            phoneme_count = word_data.get("ph_cnt", 0)
            is_unintelligible = word_data.get("unintelligible", False)
            has_equal_stress = word_data.get("equal_stress", False)
            stress_error_info = word_data.get("stress_error", {})
            
            word_analyses.append(WordAnalysis(
                word=word,
                score=score * 100,  # Convert to percentage
                word_idx=word_idx,
                phoneme_count=phoneme_count,
                ipa="",  # IPA not available in word_detail, need align_info
                is_unintelligible=is_unintelligible,
                has_equal_stress=has_equal_stress,
                stress_error_info=stress_error_info
            ))
        
        return word_analyses
    
    def _extract_phoneme_errors(self, feedback: Dict[str, Any]) -> List[PhonemeError]:
        """Extract phoneme error information from feedback.
        
        Args:
            feedback: Feedback section of API response
            
        Returns:
            List of PhonemeError objects
        """
        phoneme_errors = []
        
        # Get phone_detail from feedback
        phone_detail = feedback.get("phone_detail", []) if isinstance(feedback, dict) else []
        
        for error_data in phone_detail:
            error = PhonemeError(
                word=error_data.get("word", ""),
                word_idx=error_data.get("word_idx", 0),
                error_type=error_data.get("error_type", ""),
                error_tag=error_data.get("error_tag", ""),
                definition=error_data.get("definition", ""),
                spell_view=error_data.get("spell_view", "")
            )
            phoneme_errors.append(error)
        
        return phoneme_errors
    
    def calculate_score_percentages(self, scores: ProficiencyScores) -> Dict[str, float]:
        """Calculate percentage values for scores based on their scales.
        
        Args:
            scores: ProficiencyScores object
            
        Returns:
            Dictionary mapping score names to percentage values
        """
        percentages = {}
        
        for score_name, scale_info in SCORE_SCALES.items():
            score_value = getattr(scores, score_name, 0)
            min_val = scale_info["min"]
            max_val = scale_info["max"]
            
            # For 5-point Likert scale scores, multiply by 20 to get percentage
            if max_val == 5.0 and min_val == 1.0:
                # Convert 1-5 scale to 0-100 percentage: (score-1)/4 * 100 = (score-1) * 25
                # But simpler: score * 20 gives us the right range for display
                percentage = score_value * 20
                percentages[score_name] = max(0, min(100, percentage))
            elif max_val == 100.0:
                # Acoustic score is already 0-100
                percentage = score_value
                percentages[score_name] = max(0, min(100, percentage))
            else:
                # Fallback calculation
                if max_val > min_val:
                    percentage = ((score_value - min_val) / (max_val - min_val)) * 100
                    percentages[score_name] = max(0, min(100, percentage))
                else:
                    percentages[score_name] = score_value
        
        return percentages
    
    def get_score_color(self, percentage: float) -> str:
        """Get color for score based on percentage.
        
        Args:
            percentage: Score percentage (0-100)
            
        Returns:
            Color hex code
        """
        if percentage >= SCORE_THRESHOLDS["excellent"]:
            return SCORE_COLORS["excellent"]
        elif percentage >= SCORE_THRESHOLDS["good"]:
            return SCORE_COLORS["good"]
        else:
            return SCORE_COLORS["needs_improvement"]
    
    def get_overall_assessment(self, proficiency_scores: ProficiencyScores) -> str:
        """Generate overall assessment based on scores.
        
        Args:
            proficiency_scores: ProficiencyScores object
            
        Returns:
            Assessment string
        """
        # Calculate average percentage
        percentages = self.calculate_score_percentages(proficiency_scores)
        avg_percentage = sum(percentages.values()) / len(percentages) if percentages else 0
        
        if avg_percentage >= SCORE_THRESHOLDS["excellent"]:
            return "Excellent pronunciation!"
        elif avg_percentage >= SCORE_THRESHOLDS["good"]:
            return "Good pronunciation with room for improvement"
        else:
            return "Keep practicing to improve your pronunciation"
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return default