# Progress

## Current Status

- **Overall:** The Yad2 Apartment Notifier script appears to be largely feature-complete based on the initial requirements and the tasks marked as done in `tasks.txt`. Core functionality for fetching, parsing, filtering, and notifying is implemented.
- **Documentation:** The Memory Bank is currently being initialized. `projectbrief.md`, `productContext.md`, `techContext.md`, `systemPatterns.md`, and `activeContext.md` have been populated.

## What Works (Based on Implemented Code & `tasks.txt`)

- **Configuration:** Loading of parameters (API URL, Telegram tokens, filter criteria, bounding boxes) from `.env` file via `src/config.py`.
- **Fetching Data:** `src/fetcher.py` can retrieve data from the Yad2 API using specified URLs, parameters (including bounding boxes), and headers. It includes retry logic.
- **Parsing Data:**
    - `src/dto.py` defines `ApartmentDTO` and `AddressDTO` for structured data.
    - `src/listing_parser.py` processes the raw JSON from the fetcher, using the DTOs to create a list of apartment objects.
- **State Management:** `src/state.py` handles:
    - Loading previously sent listing IDs and timestamps from `sent_listings.json`.
    - Filtering new listings against this state.
    - Saving the updated state (with timestamps converted to ISO 8601 strings).
- **Filtering:**
    - Filters out already seen listings (via state management).
    - `main.py` implements filtering based on price, rooms, and neighborhood IDs (though neighborhood IDs might be secondary to bounding box precision).
    - The use of multiple bounding boxes (`BBOX_LIST` in `main.py`) allows for geographically targeted searches.
- **Notifications:** `src/notifier.py` can format apartment details and send notifications (text, photo, media groups) to a Telegram chat via a bot. It includes logic for message formatting and handling Telegram API responses/errors like `RetryAfter`.
- **Orchestration:** `src/main.py` successfully orchestrates the workflow: config loading -> fetching (iterating through bounding boxes) -> parsing -> de-duplication -> filtering (state & criteria) -> notifying -> state saving.
- **Asynchronous Operations:** Delays and notification sending are handled asynchronously using `asyncio` to prevent blocking and manage API rate limits.
- **Logging:** Basic logging is implemented throughout the application.
- **Command-Line Interface:** `main.py` accepts a `--test` argument for running in a limited test mode.

## What's Left to Build / Planned (from `tasks.txt`)

- **Task 3.5:** Add unit/integration tests (e.g., for parser, using `pytest`). This is the only task explicitly marked as not done in `tasks.txt` under "Feature Enhancement & Refinement".
- **Continuous Improvement:** While most core features are implemented, ongoing improvements could include:
    - More sophisticated error handling and alerting.
    - Enhanced test coverage.
    - Further optimization of API interactions if needed.
    - More flexible configuration options if new requirements arise.

## Known Issues (From a Development/Documentation Perspective)

- **Testing Gap:** Lack of formal unit/integration tests (Task 3.5) means the robustness of individual components relies on manual testing or observed behavior during runs.
- **Hardcoded Elements:** While most configurations are in `.env`, `main.py` still contains some hardcoded parameters for filters (e.g., `min_price`, `max_price`, `min_rooms`, `max_rooms`, `multi_neighborhood`, `property` types for API query) and Telegram bot token/chat ID (though these should ideally be from config and the `config.py` is set up to load them, `main.py` seems to override them for now). The `all_bbox_list` is also hardcoded in `main.py` which is less flexible than being in `.env` (though `config.py` *is* set up to load `BBOX_LIST` from `.env`).

This `progress.md` reflects the state as inferred from the project files during the Memory Bank initialization. Actual operational status would require running the script. 