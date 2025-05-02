import logging
from typing import List, Dict, Any, Optional

# Assuming dto.py is in the same directory or Python path is set correctly
from .dto import ApartmentDTO

logger = logging.getLogger(__name__)

# Path is no longer needed as we know the structure is likely root['data'][list_of_lists]
# DEFAULT_ITEMS_PATH = ['data'] # Adjusted based on API response inspection

def parse_listings(raw_data: Optional[Dict[str, Any]]) -> List[ApartmentDTO]:
    """
    Parses the raw dictionary data from the Yad2 API response to extract apartment listings.
    Assumes the structure is {"data": [[apt_dict_1, apt_dict_2, ...]]}.

    Args:
        raw_data: The dictionary parsed from the JSON response.

    Returns:
        A list of successfully parsed ApartmentDTO objects.
    """
    if not raw_data or not isinstance(raw_data, dict):
        logger.error("Parser received invalid input: raw_data is None or not a dictionary.")
        return []

    # Access the main list based on observed structure
    try:
        # --- Updated access path based on logs --- #
        data_dict = raw_data.get('data')
        if not isinstance(data_dict, dict):
            raise ValueError("Expected 'data' key to contain a dictionary.")

        listing_items = data_dict.get('markers')
        # Allow markers to be empty, just means no results
        if listing_items is None:
             logger.info("'markers' key not found within 'data'. Assuming no listings.")
             # Debugging log removed as we expect markers now
             # logger.debug(f"Full raw_data received when listings key was missing: {raw_data}")
             listing_items = []
        elif not isinstance(listing_items, list):
            # --- Update error message --- #
            raise TypeError(f"Expected 'markers' key to contain a list, but got {type(listing_items).__name__}")
        # --- End updated access path --- #

    except (KeyError, ValueError, TypeError) as e: # Removed IndexError
        # --- Update error message --- #
        logger.error(f"Could not find or access the expected list of markers within 'data['markers']'. Error: {e}")
        logger.debug(f"Raw data structure (keys): {list(raw_data.keys())}")
        # Log content of 'data' field if it exists and is a dict
        if isinstance(raw_data, dict) and 'data' in raw_data and isinstance(raw_data['data'], dict):
            logger.debug(f"Content of 'data' field (keys): {list(raw_data['data'].keys())}")
        return []

    parsed_apartments: List[ApartmentDTO] = []
    total_items = len(listing_items)
    parsed_count = 0

    logger.info(f"Found {total_items} apartment items in the list. Attempting to parse...")

    for i, item_data in enumerate(listing_items):
        if not isinstance(item_data, dict):
            logger.warning(f"Item {i+1}/{total_items} is not a dictionary, skipping. Type: {type(item_data).__name__}")
            continue

        # Attempt to parse the individual item using the DTO's class method
        apartment_dto = ApartmentDTO.from_api_data(item_data)

        if apartment_dto:
            parsed_apartments.append(apartment_dto)
            parsed_count += 1
        else:
            # Logging for failed parsing is handled within from_api_data
            logger.debug(f"Failed to parse item {i+1}/{total_items}. Item data keys: {list(item_data.keys()) if isinstance(item_data, dict) else 'N/A'}")

    logger.info(f"Successfully parsed {parsed_count}/{total_items} listings.")
    return parsed_apartments
