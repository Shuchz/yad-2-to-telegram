import json
import logging
import os
import time # Added for timestamping
from typing import Dict, List, Optional # Changed Set to Dict

from .dto import ApartmentDTO

logger = logging.getLogger(__name__)

# Default filename for storing sent listing IDs
DEFAULT_STATE_FILENAME = "sent_listings.json"

def get_state_filepath(filename: Optional[str] = None) -> str:
    """Determines the absolute path for the state file."""
    if filename is None:
        filename = DEFAULT_STATE_FILENAME
    # Place state file in the project root directory by default
    project_root = os.path.join(os.path.dirname(__file__), '..')
    return os.path.join(project_root, filename)

def load_sent_state(state_filepath: str) -> Dict[str, float]:
    """
    Loads the state dictionary (listing_id -> timestamp) from the state file.
    Handles migration from the old list format.

    Args:
        state_filepath: The path to the state file (e.g., sent_listings.json).

    Returns:
        A dictionary mapping listing IDs (str) to the timestamp (float) they were first seen/sent.
        Returns an empty dict if the file doesn't exist or is invalid.
    """
    sent_state: Dict[str, float] = {}
    if not os.path.exists(state_filepath):
        logger.info(f"State file not found at {state_filepath}. Starting with empty state.")
        return sent_state

    try:
        with open(state_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                # New format: dictionary {id: timestamp}
                sent_state = {str(k): float(v) for k, v in data.items()} # Ensure types
                logger.info(f"Loaded {len(sent_state)} sent listing states (ID -> timestamp) from {state_filepath}")
            elif isinstance(data, list):
                # Old format: list of IDs. Migrate to new format.
                current_time = time.time()
                sent_state = {str(item_id): current_time for item_id in data}
                logger.warning(f"Detected old state format (list) in {state_filepath}. Migrated {len(sent_state)} IDs to new format (ID -> timestamp) using current time.")
                # Optionally: Trigger a save immediately after migration?
                # save_sent_state(sent_state, state_filepath) # Consider this if you want to force update the file format
            else:
                logger.warning(f"Invalid format in state file {state_filepath}. Expected a dict or list, got {type(data)}. Resetting state.")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from state file {state_filepath}. File might be corrupted. Resetting state.")
    except Exception as e:
        logger.error(f"Failed to load state file {state_filepath}: {e}", exc_info=True)

    return sent_state

def save_sent_state(sent_state: Dict[str, float], state_filepath: str) -> bool:
    """
    Saves the current state dictionary (listing_id -> timestamp) to the state file.

    Args:
        sent_state: The dictionary mapping IDs to timestamps to save.
        state_filepath: The path to the state file.

    Returns:
        True if saving was successful, False otherwise.
    """
    try:
        # Sort by timestamp for potential readability, though dict order isn't guaranteed in older Python < 3.7
        # For consistency, maybe sort by ID? Let's sort by ID.
        items_to_save = sorted(sent_state.items())
        state_to_save_ordered = {k: v for k, v in items_to_save}

        with open(state_filepath, 'w', encoding='utf-8') as f:
            json.dump(state_to_save_ordered, f, indent=4)
        logger.info(f"Successfully saved state for {len(sent_state)} listings to {state_filepath}")
        return True
    except IOError as e:
        logger.error(f"Failed to write to state file {state_filepath}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving state to {state_filepath}: {e}", exc_info=True)
        return False

def filter_new_listings(listings: List[ApartmentDTO], sent_state: Dict[str, float]) -> List[ApartmentDTO]:
    """
    Filters out listings that have already been sent based on the sent_state dictionary.

    Args:
        listings: A list of ApartmentDTO objects to filter.
        sent_state: A dictionary where keys are listing IDs and values are timestamps of when they were sent.

    Returns:
        A list of ApartmentDTO objects that are new (not in sent_state).
    """
    new_listings = []
    for listing in listings:
        if listing.id not in sent_state:
            new_listings.append(listing)

    return new_listings

# Add a function to update sent listings in batches
def update_sent_listings_in_batches(sent_listings: dict, new_listings: list, batch_size: int = 5):
    """Update sent listings in batches to avoid large writes."""
    for i in range(0, len(new_listings), batch_size):
        batch = new_listings[i:i + batch_size]
        for listing in batch:
            sent_listings[listing['id']] = listing['timestamp']

        # Save the updated sent listings to the file after each batch
        with open('sent_listings.json', 'w') as file:
            json.dump(sent_listings, file, indent=4)

        logger.info(f"Updated sent listings with batch {i // batch_size + 1} containing {len(batch)} listings.")
