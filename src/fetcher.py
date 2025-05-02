import requests
import logging
import time # Added for sleep
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# --- Use a Session for connection pooling and cookie persistence ---
session = requests.Session()
# Apply default headers to the session
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})
# --- End Session Setup ---

DEFAULT_TIMEOUT = 15 # seconds
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

def fetch_yad2_data(base_url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
    """
    Fetches data from the specified Yad2 API base URL and parameters using a requests.Session.
    Includes basic retry logic.

    Args:
        base_url: The base Yad2 API endpoint URL (without query parameters).
        params: Optional dictionary of query parameters to send with the request.
        headers: Optional dictionary of *additional* HTTP headers to send with the request
                 (will be merged with session headers, overriding if keys conflict).
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the parsed JSON response, or None if an error occurs after retries.
    """
    # Create a mutable dictionary for request-specific headers
    request_headers = headers.copy() if headers else {}

    if params is None:
        params = {} # Ensure params is a dict for the request call

    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        # Construct the full URL for logging purposes
        try:
            # Prepare the request to get the full URL easily
            prepared_request = requests.Request('GET', base_url, params=params, headers=request_headers).prepare()
            # Merge session headers with request-specific headers for logging/actual request
            # Request-specific headers take precedence
            final_headers = session.headers.copy()
            final_headers.update(request_headers) # Apply request-specific headers
            prepared_request.headers = final_headers # Update prepared request for logging

            full_url_for_log = prepared_request.url
            logger.info(f"Attempting to fetch data (Attempt {attempt}/{MAX_RETRIES}) from: {full_url_for_log}")

            # --- Use session.get instead of requests.get ---
            logger.debug(f"Making request to base_url: {base_url} with params: {params} and merged headers: {final_headers}")
            response = session.get(base_url, params=params, headers=final_headers, timeout=timeout)
            # --- End session.get usage ---

            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            # Check if content type is JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                # Check for common CAPTCHA/block indicators
                if 'text/html' in content_type and ('Captcha' in response.text or 'Are you for real' in response.text):
                     logger.error(f"Received HTML content, likely a CAPTCHA or block page from {full_url_for_log}. Cannot proceed with requests. Status: {response.status_code}. Not retrying.")
                     return None # Don't retry CAPTCHAs
                else:
                     logger.warning(f"Unexpected content type '{content_type}' received from {full_url_for_log}. Attempting to parse as JSON anyway.")

            data = response.json()
            logger.info(f"Successfully fetched and parsed JSON data from {full_url_for_log}.")
            return data # Success, exit loop

        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timed out (Attempt {attempt}/{MAX_RETRIES}) for URL: {full_url_for_log}. Error: {e}")
            if attempt == MAX_RETRIES:
                 logger.error("Max retries reached for Timeout error.")
                 return None
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Status Code: {response.status_code} for {full_url_for_log}. Not retrying.")
            return None
        except requests.exceptions.RequestException as req_err:
            logger.warning(f"Request error occurred (Attempt {attempt}/{MAX_RETRIES}) for {full_url_for_log}: {req_err}")
            if attempt == MAX_RETRIES:
                 logger.error("Max retries reached for RequestException.")
                 return None
        except requests.exceptions.JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON response from {full_url_for_log}. Error: {json_err}. Not retrying.")
            logger.debug(f"Response text that failed parsing: {response.text[:500]}...")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching {full_url_for_log}: {e}. Not retrying.", exc_info=True)
            return None

        # If we reached here, it was a potentially transient error
        logger.info(f"Waiting {RETRY_DELAY_SECONDS} seconds before next retry...")
        time.sleep(RETRY_DELAY_SECONDS)

    logger.error(f"Exited fetch loop unexpectedly after max retries for {full_url_for_log}.")
    return None
