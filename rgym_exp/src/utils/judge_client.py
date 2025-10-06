import requests
from typing import Dict, Any, Optional
from genrl.logging_utils.global_defs import get_logger


class JudgeClient:
    """
    Client for interacting with the judge API service.
    Handles question requests and answer submissions.
    """
    
    def __init__(self, base_url: str):
        """
        Initialize the judge client.
        
        Args:
            base_url: Base URL for the judge API service
        """
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger()
    
    def request_question(self, user_id: str, round_number: int, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Request a question from the judge service.
        
        Args:
            user_id: ID of the user/peer
            round_number: Current round number
            model_name: Name of the model being used
            
        Returns:
            Dictionary containing question data or None if request failed
        """
        try:
            request_data = {
                "user_id": user_id,
                "round_number": round_number,
                "model_name": model_name,
            }
            
            response = requests.post(
                f"{self.base_url}/request-question/", 
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f'Received question: {result.get("question", "N/A")}')
                return result
            else:
                self.logger.warning(f"Failed to receive question: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error requesting question: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error requesting question: {e}")
            return None
    
    def get_current_clue(self) -> Optional[Dict[str, Any]]:
        """
        Get the current clue from the judge service.
        
        Returns:
            Dictionary containing clue data or None if request failed
        """
        try:
            response = requests.get(f"{self.base_url}/current_clue/")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f'Received clue: {result.get("clue", "N/A")}')
                return result
            else:
                self.logger.warning(f"Failed to receive clue: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error getting current clue: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting current clue: {e}")
            return None
        

    def submit_answer(self, session_id: str, round_number: int, user_answer: str) -> Optional[Dict[str, Any]]:
        """
        Submit an answer to the judge service.
        
        Args:
            session_id: Session ID from the question request
            round_number: Current round number
            user_answer: The user's answer to submit
            
        Returns:
            Dictionary containing score data or None if submission failed
        """
        try:
            submission_data = {
                "session_id": session_id,
                "round_number": round_number,
                "user_answer": user_answer,
            }

            response = requests.post(
                f"{self.base_url}/submit-answer/", 
                json=submission_data
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Score: {result.get('score', 'N/A')}")
                return result
            else:
                self.logger.warning(f"Failed to submit answer: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error submitting answer: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error submitting answer: {e}")
            return None