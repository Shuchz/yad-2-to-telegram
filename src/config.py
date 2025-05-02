import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)

# Define expected environment variables and their types/defaults
ENV_VARS = {
    "YAD2_URL": (str, "https://gw.yad2.co.il/realestate-feed/rent/map"), # Base URL, required
    "TELEGRAM_BOT_TOKEN": (str, None),             # Required string
    "TELEGRAM_CHAT_ID": (str, None),               # Required string
    "LOG_LEVEL": (str, "INFO"),                    # Optional string, default INFO
    # API Parameters (Optional, default to None for no filter)
    # BBOX_LIST: Semicolon-separated list of bounding boxes. E.g., "lat1,lon1,lat2,lon2;lat3,lon3,lat4,lon4"
    "BBOX_LIST": (str, None),
    "MIN_PRICE": (int, None),                    # Optional integer
    "MAX_PRICE": (int, None),                    # Optional integer
    "MIN_ROOMS": (Union[int, float], None),      # Optional number (can be float like 2.5)
    "MAX_ROOMS": (Union[int, float], None),      # Optional number
    "MULTI_NEIGHBORHOOD": (str, None),           # Optional comma-separated string of IDs, e.g., "1461,1520" (May be redundant if BBOX_LIST is precise)
    "DEFAULT_ZOOM": (int, 15),                   # Optional zoom level, defaults to 15 based on curl
    # ZOOM is no longer used, bounding boxes define the view
}

def parse_env_var(value: Optional[str], expected_type: Union[type, tuple]) -> Any: # Allow tuple for Union
    """Parses an environment variable string into the expected type."""
    if value is None:
        return None

    try:
        # Handle Union types (specifically for rooms)
        if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
             # Try parsing as float first (covers int and float), then fallback could be added if needed
            try:
                return float(value)
            except ValueError:
                logger.warning(f"Failed to parse room value '{value}' as float.")
                return None

        if expected_type is int:
            return int(value)
        # Removed list parsing as MULTI_NEIGHBORHOOD is now a string
        # if expected_type is list:
        #     return [item.strip() for item in value.split(',') if item.strip()]
        # Default is string, no conversion needed
        return value
    except ValueError as e:
        logger.warning(f"Failed to parse environment variable value '{value}' as {expected_type}: {e}")
        return None # Return None if parsing fails

def load_config() -> Dict[str, Any]:
    """
    Loads configuration from environment variables.

    Looks for a .env file first, then checks system environment variables.
    Validates that required variables are set and parses types.

    Returns:
        A dictionary containing the configuration values with correct types.
    """
    # Load .env file if it exists
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Look for .env in root
    if os.path.exists(dotenv_path):
        logger.info(f"Loading environment variables from: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        logger.info(".env file not found, relying on system environment variables.")
        load_dotenv() # Still load system vars

    config: Dict[str, Any] = {}
    # Define the truly required variables
    required_vars = ["YAD2_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "BBOX_LIST"]
    missing_vars = []

    for var_name, (expected_type, default_value) in ENV_VARS.items():
        raw_value = os.getenv(var_name)
        parsed_value = parse_env_var(raw_value, expected_type)

        # Use default if parsing failed or var not set
        if parsed_value is None and default_value is not None:
            # Handle cases where default needs parsing too (e.g., default int)
            if isinstance(default_value, str) and expected_type != str and not (hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union):
                config[var_name] = parse_env_var(default_value, expected_type)
            else:
                config[var_name] = default_value
        else:
            config[var_name] = parsed_value

        # Check if REQUIRED variables are missing
        if var_name in required_vars and config[var_name] is None:
            missing_vars.append(var_name)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        # Consider raising an exception or returning None/empty dict for critical failures
        # raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return {} # Return empty dict to signal critical failure

    logger.info("Configuration loaded successfully.")
    # Log loaded config excluding sensitive token
    log_config = {k: v for k, v in config.items() if k != 'TELEGRAM_BOT_TOKEN'}
    logger.debug(f"Loaded config: {log_config}")

    return config

# Example usage:
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     app_config = load_config()
#     if app_config.get("TELEGRAM_BOT_TOKEN"):
#         print("Config loaded.")
#         print(f"Max Price: {app_config.get('MAX_PRICE')}")
#         print(f"Allowed Neighborhoods: {app_config.get('MULTI_NEIGHBORHOOD')}")
#     else:
#         print("Config loading failed or required vars missing.")
