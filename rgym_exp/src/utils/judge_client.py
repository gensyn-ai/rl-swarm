import requests
from requests.adapters import HTTPAdapter
try:
    # Try modern import path first (urllib3 2.0+)
    from urllib3.util.retry import Retry
except ImportError:
    # Fallback to legacy import path (older versions)
    from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Any, Optional
import time
import socket
from genrl.logging_utils.global_defs import get_logger


class SocketOptionsHTTPAdapter(HTTPAdapter):
    """
    Custom HTTPAdapter that supports socket options.

    The socket_options parameter is not directly supported by requests.adapters.HTTPAdapter,
    but can be implemented by overriding init_poolmanager to pass options to urllib3.
    """

    def __init__(self, socket_options=None, *args, **kwargs):
        self.socket_options = socket_options
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.socket_options is not None:
            kwargs["socket_options"] = self.socket_options
        return super().init_poolmanager(*args, **kwargs)


class JudgeClient:
    """
    Client for interacting with the judge API service.
    Handles question requests and answer submissions with connection pooling and retry logic.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the judge client with performance optimizations.

        Args:
            base_url: Base URL for the judge API service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger()
        self.timeout = timeout

        # Set up session with connection pooling and retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # Total number of retries
            backoff_factor=1,  # Wait time multiplier between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        # Configure connection adapter with pooling and socket options
        adapter = SocketOptionsHTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,  # Max connections per pool
            socket_options=[(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)]  # SO_REUSEADDR
        )

        # Mount adapter for both HTTP and HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set session headers for keep-alive
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'rl-swarm-judge-client/1.0'
        })

    def __del__(self):
        """Clean up session resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
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

            response = self.session.post(
                f"{self.base_url}/request-question/",
                json=request_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f'Received question: {result["question"]}')
                return result
            else:
                self.logger.debug(f"Failed to receive question: {response.status_code}")
                return None

        except Exception as e:
            self.logger.debug(f"Failed to request question: {e}")
            return None
    
    def get_current_clue(self) -> Optional[Dict[str, Any]]:
        """
        Get the current clue from the judge service.

        Returns:
            Dictionary containing clue data or None if request failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/current_clue/",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f'Received clue: {result["clue"]}')
                return result
            else:
                self.logger.debug(f"Failed to receive clue: {response.status_code}")
                return None

        except Exception as e:
            self.logger.debug(f"Failed to get current clue: {e}")
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

            response = self.session.post(
                f"{self.base_url}/submit-answer/",
                json=submission_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Score: {result['score']}")
                return result
            else:
                self.logger.debug(f"Failed to submit answer: {response.status_code}")
                return None

        except Exception as e:
            self.logger.debug(f"Failed to submit answer: {e}")
            return None