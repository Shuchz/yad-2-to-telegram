# Add project root directory to sys.path before any imports
import sys
sys.path.insert(0, '/Users/zeev/Desktop/code/yad-2-to-telegram')

import logging
import time
import asyncio
import argparse # Import argparse
from typing import List, Optional, Set, Dict
# Remove urlencode import as we'll build params dict directly
# from urllib.parse import urlencode

# Assuming components are in the src directory relative to the project root
# REMOVE: from . import config
from src import fetcher
from src import listing_parser
from src import notifier
from src import state
from src.dto import ApartmentDTO
import telegram
from src.state import update_sent_listings_in_batches
# Import mongo_repository for MongoDB integration
from repositories import mongo_repository
# Import MongoDB functions for managing seen apartments
from migrate_sent_listings import is_apartment_seen, add_seen_apartment, get_all_seen_apartment_ids, string_to_numeric_id

# Basic Logging Configuration
logging.basicConfig(
    level=logging.DEBUG, # Changed to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
        # Consider adding logging.FileHandler('app.log') later
    ]
)

logger = logging.getLogger(__name__)

# Optional: Define a polling interval if running continuously
POLLING_INTERVAL_SECONDS = 1800 # 5 minutes -> 30 minutes (1800 seconds)
TEST_MODE_NOTIFICATION_LIMIT = 2 # Max notifications in test mode

# --- Modify run_check to accept test mode flag --- #
async def run_check(is_test_mode: bool = False) -> None:
    """Performs a single check: fetch, parse, filter, notify, save state (async)."""
    # Define bot_token and chat_id at the very beginning of the function
    bot_token = "7684767205:AAE3HVDNwO62Y0fAo-u5bdYPq0gt6L3_awA"
    chat_id = "-4741762001"

    if is_test_mode:
        logger.info("Starting apartment check run in TEST MODE...")
    else:
        logger.info("Starting apartment check run...")

    # Send "Search Initiated" message to Telegram group
    await notifier.send_telegram_message(bot_token, chat_id, "*Search Initiated*")
    await asyncio.sleep(1) # Add 60-second delay

    # --- State File Setup --- Changed to load state dict ---
    state_filepath = state.get_state_filepath() # Use default filename
    # sent_ids: Set[str] = state.load_sent_ids(state_filepath)
    sent_state: Dict[str, float] = state.load_sent_state(state_filepath) # Use new load function
    initial_sent_count = len(sent_state)

    # --- Hardcoded Configuration ---
    # REMOVED: app_config = config.load_config()
    base_yad2_url = "https://gw.yad2.co.il/realestate-feed/rent/map" # Correct base URL
    # !!! REPLACE THESE WITH YOUR ACTUAL VALUES !!!
    # !!! END REPLACE SECTION !!!

    # Parameters from the specific URL provided
    min_price = 4000
    max_price = 8000
    min_rooms = 2
    max_rooms = 4
    multi_neighborhood = "1461,1520" # Add example neighborhood IDs
    # REMOVED: specific_bbox = "32.066111,34.765788,32.070878,34.786357" # Specific box from URL
    # --- Bounding Box List (Replace/Refine based on testing) ---
    all_bbox_list = [
        "32.075192,34.763754,32.086468,34.779760",
        "32.075076,34.771885,32.086353,34.787891",
        "32.076017,34.781501,32.084821,34.793997",
        "32.080523,34.782766,32.088978,34.794767",
        "32.068977,34.760081,32.081317,34.777596",
        "32.067273,34.764900,32.079614,34.782414",
        "32.065226,34.770869,32.077566,34.788383",
        "32.064591,34.775937,32.076932,34.793451",
        "32.060576,34.760166,32.071472,34.775629",
        "32.057632,34.767177,32.068528,34.782639",
        "32.052334,34.760749,32.063151,34.776098",
        # Add the previously hardcoded one as well, just in case
        "32.066111,34.765788,32.070878,34.786357"
    ]
    default_zoom = 15 # Adjusted based on most URLs, can be tuned
    fetch_delay_seconds = 4 # Increased delay between API calls for stealth

    # --- Use only first bbox if in test mode --- #
    bbox_list_to_use = all_bbox_list[:1] if is_test_mode else all_bbox_list
    if is_test_mode:
        logger.warning(f"TEST MODE: Using only the first bounding box: {bbox_list_to_use[0]}")

    # Check critical hardcoded values (removed specific_bbox check)
    if not all([base_yad2_url, bot_token, chat_id]) or \
       bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or \
       chat_id == "YOUR_TELEGRAM_CHAT_ID_HERE":
        logger.critical("Missing critical hardcoded configuration (URL, Token, or Chat ID), or placeholders not replaced. Exiting.")
        return

    # --- Define fixed headers (from curl) ---
    # Assuming fetcher will be updated to accept headers
    request_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.yad2.co.il',
        'Referer': 'https://www.yad2.co.il/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    # --- Fetch and process data for selected bounding boxes ---
    all_listings_aggregated: List[ApartmentDTO] = [] # Initialize list to store all results
    total_fetched = 0

    # --- Loop over the selected bbox list --- #
    for i, current_bbox in enumerate(bbox_list_to_use):
        logger.info(f"Fetching data for bbox {i+1}/{len(bbox_list_to_use)}: {current_bbox}...")
        # Construct parameters for this specific box
        api_params = {
            # Keep other params constant for now, refine if needed
            "multiNeighborhood": multi_neighborhood,
            "minPrice": min_price,
            "maxPrice": max_price,
            "minRooms": min_rooms,
            "maxRooms": max_rooms,
            "property": "1,3,6,7,25,49,51,11,31,43,4", # From example URLs
            "bBox": current_bbox,                # Use current box from list
            "zoom": default_zoom                 # Use common zoom
        }
        # Filter out None values (though none are None in this case)
        filtered_params = {k: v for k, v in api_params.items() if v is not None}

        # Fetch data for the specific parameters
        raw_data = fetcher.fetch_yad2_data(base_yad2_url, params=filtered_params, headers=request_headers)

        if not raw_data:
            logger.warning(f"Failed to fetch data for bbox: {current_bbox}. Skipping this box.")
        else:
            # Parse listings
            listings_from_fetch: List[ApartmentDTO] = listing_parser.parse_listings(raw_data)
            if listings_from_fetch:
                count = len(listings_from_fetch)
                logger.info(f"Parsed {count} listings for bbox: {current_bbox}.")
                all_listings_aggregated.extend(listings_from_fetch) # Add to the main list
                total_fetched += count
            else:
                logger.info(f"No listings parsed for bbox: {current_bbox}.")

        # Add a delay before the next request (only relevant if not test mode or list > 1)
        if i < len(bbox_list_to_use) - 1:
            logger.debug(f"Waiting {fetch_delay_seconds} seconds before next fetch...")
            await asyncio.sleep(fetch_delay_seconds)

    # --- End Fetch Loop ---
    logger.info(f"Finished fetching. Total listings fetched across all bboxes (before deduplication): {total_fetched}")

    # If no listings found across all fetches
    if not all_listings_aggregated:
        logger.info("No listings found or parsed across any specified bounding boxes.")
        # Save state even if no listings found (handles potential format migration on load)
        # state.save_sent_ids(sent_ids, state_filepath)
        state.save_sent_state(sent_state, state_filepath) # Use new save function
        return

    # 3. De-duplicate Aggregated Listings
    unique_listings_map = {apt.id: apt for apt in all_listings_aggregated}
    unique_listings = list(unique_listings_map.values())
    logger.info(f"Total unique apartments found after aggregation and deduplication: {len(unique_listings)}")

    # No need to check if unique_listings is empty again, handled above

    # 4. Retrieve all seen apartment IDs from MongoDB at once
    seen_apartment_ids = get_all_seen_apartment_ids()
    logger.info(f"Retrieved {len(seen_apartment_ids)} already seen apartment IDs from MongoDB")
    
    # Filter new listings using in-memory comparison (much faster)
    new_apartments = []
    for apt in unique_listings:
        # Convert apartment ID to numeric ID for comparison
        numeric_id = string_to_numeric_id(apt.id)
        if numeric_id not in seen_apartment_ids:
            new_apartments.append(apt)
    
    logger.info(f"Found {len(new_apartments)}/{len(unique_listings)} new apartments after filtering against MongoDB seen_apartments collection")

    if not new_apartments:
        logger.info("No *new* apartments found to notify.")
        # Save state even if no new listings found
        # state.save_sent_ids(sent_ids, state_filepath)
        state.save_sent_state(sent_state, state_filepath) # Use new save function
        return

    logger.info(f"Found {len(new_apartments)} new apartments potentially matching criteria.")

    # --- Limit notifications in test mode --- #
    apartments_to_notify = new_apartments
    if is_test_mode:
        if len(new_apartments) > TEST_MODE_NOTIFICATION_LIMIT:
            logger.warning(f"TEST MODE: Limiting notifications to {TEST_MODE_NOTIFICATION_LIMIT} out of {len(new_apartments)} new apartments found.")
            apartments_to_notify = new_apartments[:TEST_MODE_NOTIFICATION_LIMIT]
        else:
            logger.info(f"TEST MODE: Found {len(new_apartments)} new apartments (within limit of {TEST_MODE_NOTIFICATION_LIMIT}).")

    logger.info(f"Attempting to notify for {len(apartments_to_notify)} apartments.")

    # Add a begin message before starting the notification process
    logger.info("Starting the notification process...")

    # Initialize counters for success and failure
    success_count = 0
    failure_count = 0
    mongo_success_count = 0  # Track MongoDB saves
    
    # Store successfully notified apartments to batch process later
    notified_apartment_ids = []

    # Add batching logic to send notifications in batches with delays
    async def send_notifications_in_batches(apartments_to_notify: List[ApartmentDTO], bot_token: str, chat_id: str, batch_size: int = 5, delay_between_batches: int = 10):
        """Send notifications in batches to avoid hitting rate limits."""
        nonlocal success_count, failure_count, mongo_success_count, notified_apartment_ids
        total_apartments = len(apartments_to_notify)
        for i in range(0, total_apartments, batch_size):
            batch = apartments_to_notify[i:i + batch_size]
            logger.info(f"Sending batch {i // batch_size + 1} with {len(batch)} apartments...")

            for apt in batch:
                try:
                    # Save the apartment to MongoDB before sending the notification
                    try:
                        mongo_repository.save_apartment(apt)
                        logger.info(f"Successfully saved apartment {apt.id} to MongoDB.")
                        mongo_success_count += 1
                    except Exception as mongo_err:
                        logger.error(f"Failed to save apartment {apt.id} to MongoDB: {mongo_err}")
                        # Continue with notification even if MongoDB save fails
                    
                    if await notifier.send_telegram_notification(bot_token, chat_id, apt):
                        logger.debug(f"Notification for {apt.id} successful.")
                        success_count += 1
                        # Add to list of successfully notified apartments
                        notified_apartment_ids.append(apt.id)
                    else:
                        logger.warning(f"Notifier returned False for apartment {apt.id}.")
                        failure_count += 1
                except telegram.error.RetryAfter as e:
                    wait_time = e.retry_after + 1
                    logger.warning(f"Rate limit hit for {apt.id}. Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Unexpected error during notification attempt for {apt.id}: {e}", exc_info=True)
                    failure_count += 1
                await asyncio.sleep(60) # Reduced delay to 10 seconds between notifications

            # Mark all successfully notified apartments as seen in MongoDB
            batch_success_ids = notified_apartment_ids.copy()
            notified_apartment_ids = []  # Clear the list for next batch
            
            if batch_success_ids:
                logger.info(f"Marking {len(batch_success_ids)} successfully notified apartments as seen in MongoDB")
                for apt_id in batch_success_ids:
                    try:
                        add_seen_apartment(apt_id)
                    except Exception as e:
                        logger.error(f"Failed to mark apartment {apt_id} as seen in MongoDB: {e}")

            # Update sent listings in batches after each notification batch
            update_sent_listings_in_batches(sent_state, [{'id': apt_id, 'timestamp': time.time()} for apt_id in batch_success_ids])

            if i + batch_size < total_apartments:
                logger.info(f"Waiting {delay_between_batches} seconds before sending the next batch...")
                await asyncio.sleep(delay_between_batches)

    # Replace the notification loop with the batching logic
    # 5. Notify about Listings to Notify
    if apartments_to_notify:
        await send_notifications_in_batches(apartments_to_notify, bot_token, chat_id)
    else:
        logger.info("No apartments to notify.")

    # Add an end message after completing the notification process
    logger.info("Notification process completed.")

    # Send "Search Finished" message to Telegram group with the current count
    current_count = len(sent_state)
    await asyncio.sleep(60) # Add 60-second delay
    await notifier.send_telegram_message(bot_token, chat_id, f"*Search Finished* - {success_count} new apartments sent in this iteration. Total listings tracked: {current_count}")

    logger.info("Notification process completed.")

    logger.info(f"Notification summary: {success_count} sent, {failure_count} failed, {mongo_success_count} saved to MongoDB.")

    # 6. Save Updated State (Always saves state, even in test mode) --- Use sent_state ---
    if len(sent_state) > initial_sent_count:
        # logger.info(f"Attempting to save updated state with {len(sent_ids)} total sent IDs.")
        logger.info(f"Attempting to save updated state with {len(sent_state)} total sent IDs and timestamps.") # Updated log
        # state.save_sent_ids(sent_ids, state_filepath)
        state.save_sent_state(sent_state, state_filepath) # Use new save function
    else:
        logger.info(f"No changes detected in sent state ({len(sent_state)} entries). No save needed unless format migration occurred.")

    # Save the state regardless of changes, as load might have migrated format
    logger.info(f"Attempting to save state for {len(sent_state)} listings to {state_filepath}")
    if not state.save_sent_state(sent_state, state_filepath):
         logger.error("Failed to save the updated state file!")
    # Removed the old save_sent_ids call

    logger.info("Apartment check run finished.")


if __name__ == "__main__":
    # --- Add argparse --- #
    parser = argparse.ArgumentParser(description="Yad2 Apartment Notifier Script")
    parser.add_argument("--test", action="store_true", help="Run in test mode (1 bbox, max 2 notifications)")
    args = parser.parse_args()
    # --- End argparse --- #

    if args.test:
        logger.info("Starting Yad2 Apartment Notifier script in TEST MODE.")
    else:
        logger.info("Starting Yad2 Apartment Notifier script.")

    print("sys.path:", sys.path)

    # Option 1: Run once using asyncio, passing test flag
    asyncio.run(run_check(is_test_mode=args.test))

    # Option 2: Run continuously (Needs async loop modification for test mode)
    # async def main_loop(is_test_mode_loop = False):
    #     while True:
    #         try:
    #             await run_check(is_test_mode=is_test_mode_loop) # Pass test flag
    #         except Exception as e:
    #             logger.critical(f"An unhandled error occurred in the main loop: {e}", exc_info=True)
    #         logger.info(f"Waiting for {POLLING_INTERVAL_SECONDS} seconds before next check...")
    #         await asyncio.sleep(POLLING_INTERVAL_SECONDS)
    # asyncio.run(main_loop(is_test_mode_loop=args.test))

    logger.info("Yad2 Apartment Notifier script finished.")
