"""API client for Phonics pronunciation evaluation service."""

import base64
import json
import logging
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.constants import API_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

class PronunciationAPIError(Exception):
    """Custom exception for API-related errors."""
    pass

class PronunciationAPI:
    """Client for interacting with the Phonics pronunciation API."""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """Initialize the API client.
        
        Args:
            api_url: The API endpoint URL
            api_key: Optional API key for authentication
        """
        self.api_url = api_url
        self.api_key = api_key
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key
    
    def encode_audio_to_base64(self, audio_data: Union[bytes, bytearray]) -> str:
        """Encode audio data to base64 string.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Base64 encoded string
        """
        try:
            return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding audio to base64: {e}")
            raise PronunciationAPIError(f"Failed to encode audio: {str(e)}")
    
    def analyze_pronunciation(self, 
                            audio_data: Union[bytes, bytearray], 
                            reference_text: str,
                            language_code: str = "english",
                            user: str = "poly") -> Dict[str, Any]:
        """Analyze pronunciation of audio against reference text.
        
        Args:
            audio_data: Raw audio bytes
            reference_text: The text that was read
            language_code: Language code for analysis
            user: User identifier
            
        Returns:
            API response as dictionary
            
        Raises:
            PronunciationAPIError: If API request fails
        """
        # Encode audio to base64
        audio_base64 = self.encode_audio_to_base64(audio_data)
        
        # Prepare request payload
        payload = {
            "argument": {
                "language_code": language_code,
                "user": user,
                "reference": reference_text,
                "audio": audio_base64
            }
        }
        
        try:
            # Make API request
            response = self.session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=API_TIMEOUT
            )
            
            # Handle response
            return self.handle_api_response(response)
            
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            raise PronunciationAPIError("Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to API")
            raise PronunciationAPIError("Failed to connect to the API. Please check your connection.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise PronunciationAPIError(f"API request failed: {str(e)}")
    
    def handle_api_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle and validate API response.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed response data
            
        Raises:
            PronunciationAPIError: If response is invalid
        """
        try:
            # Check HTTP status
            if response.status_code == 401:
                raise PronunciationAPIError("Authentication failed. Please check your API key.")
            elif response.status_code == 400:
                raise PronunciationAPIError("Invalid request. Please check your input.")
            elif response.status_code == 413:
                raise PronunciationAPIError("Audio file is too large. Please use a shorter recording.")
            elif response.status_code >= 500:
                raise PronunciationAPIError("Server error. Please try again later.")
            elif response.status_code != 200:
                raise PronunciationAPIError(f"Unexpected status code: {response.status_code}")
            
            # Parse JSON response
            data = response.json()
            
            # Log the response for debugging
            logger.info(f"API Response status: {response.status_code}")
            logger.info(f"API Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Validate response structure
            if not isinstance(data, dict):
                raise PronunciationAPIError("Invalid response format")
            
            # Check for API-level errors
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                raise PronunciationAPIError(f"API error: {error_msg}")
            
            # The API returns the data directly without a 'data' wrapper
            # Check if the response has the expected fields directly
            if "general_comment" in data or "feedback" in data or "proficiencyScore" in data:
                # Wrap in 'data' key for consistency with our processor
                return {"data": data}
            
            # Check for required fields
            if "data" not in data:
                logger.error(f"Full API response: {json.dumps(data, indent=2)[:500]}...")  # Log first 500 chars
                raise PronunciationAPIError("Response missing expected fields")
            
            return data
            
        except json.JSONDecodeError:
            logger.error("Failed to parse API response as JSON")
            raise PronunciationAPIError("Invalid response format from API")
        except PronunciationAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error handling response: {e}")
            raise PronunciationAPIError(f"Failed to process API response: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test API connection with a minimal request.
        
        Returns:
            True if connection is successful
        """
        try:
            response = self.session.get(
                self.api_url.replace("/api/phonics", "/health"),
                headers=self.headers,
                timeout=5
            )
            return response.status_code in [200, 404]  # 404 is OK if health endpoint doesn't exist
        except:
            return False