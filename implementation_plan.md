# Implementation Plan

## Phase 1: Save Timestamps as Readable Date-Time Strings in `sent_listings.json`

*   **Subtask 1.1: Modify `src/state.py` - `save_sent_state` function**
    *   Import `datetime` from the `datetime` module.
    *   Before calling `json.dump`, iterate through the `state_to_save_ordered` dictionary. For each entry, convert the float timestamp value to a human-readable ISO 8601 formatted string (e.g., using `datetime.fromtimestamp(timestamp_float).isoformat()`).
*   **Subtask 1.2: Modify `src/state.py` - `load_sent_state` function**
    *   Import `datetime` from the `datetime` module.
    *   When processing the loaded `data` (if it's a dictionary):
        *   For each value `v` associated with a listing ID:
            *   If `v` is a string, attempt to parse it back into a float timestamp using `datetime.fromisoformat(v).timestamp()`.
            *   If `v` is already a float (to support backward compatibility with existing files), use it directly.
            *   Implement error handling (e.g., `try-except ValueError`) for the string parsing. If parsing fails, log a warning and decide on a fallback (e.g., skip the entry or use the current time as the timestamp).
    *   Ensure that when migrating from the old list format, the generated timestamps (which are floats) are correctly handled by the internal logic, knowing that `save_sent_state` will convert them to strings on the next save.
*   **Subtask 1.3: Modify `src/state.py` - `update_sent_listings_in_batches` function**
    *   Remove the direct file writing block: `with open('sent_listings.json', 'w') as file: json.dump(sent_listings, file, indent=4)`.
    *   This function will now only update the `sent_listings` dictionary (which is `sent_state` passed from `main.py`) in memory. The `listing['timestamp']` (which is `time.time()`, a float) will be added as a float.
    *   The conversion to ISO string and actual file persistence will be handled by the main `save_sent_state` function (modified in Subtask 1.1) when it's called from `main.py`.

## Phase 2: Introduce 1-Minute Delays Between Telegram Notifications

*   **Subtask 2.1: Modify `src/main.py` - `run_check` function (for "Search Initiated")**
    *   Locate the line where the "Search Initiated" message is sent: `await notifier.send_telegram_message(bot_token, chat_id, "*Search Initiated*")`.
    *   Immediately after this line, add `await asyncio.sleep(60)` to introduce a 60-second delay.
*   **Subtask 2.2: Modify `src/main.py` - `send_notifications_in_batches` function (for individual apartment notifications)**
    *   Inside the `for apt in batch:` loop, after the `try-except` block that handles `notifier.send_telegram_notification`, add `await asyncio.sleep(60)`. This will create a 60-second pause after attempting to send each apartment's notification, before processing the next apartment in the batch or moving to the delay between batches.
*   **Subtask 2.3: Modify `src/main.py` - `run_check` function (for "Search Finished")**
    *   Locate the line where the "Search Finished" message is sent (this line will also be modified in Phase 3).
    *   Immediately before this line, add `await asyncio.sleep(60)`.

## Phase 3: Enhance "Search Finished" Message with New Apartment Count

*   **Subtask 3.1: Modify `src/main.py` - `run_check` function**
    *   The variable `success_count` already tracks the number of new apartments for which notifications were successfully sent in the current iteration.
    *   Modify the "Search Finished" message to include `success_count`.
    *   Change the message from:
        `await notifier.send_telegram_message(bot_token, chat_id, f"*Search Finished* - Current amount saw is {current_count}")`
        to:
        `await notifier.send_telegram_message(bot_token, chat_id, f"*Search Finished* - {success_count} new apartments sent in this iteration. Total listings tracked: {current_count}")`
    *   Ensure `current_count` (derived from `len(sent_state)`) accurately reflects the total number of listings tracked after the current iteration's updates.
