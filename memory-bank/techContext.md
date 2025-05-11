# Tech Context

## Core Technologies

- **Primary Language:** Python (version 3.x assumed)
- **Package Management:** `pip` with a `requirements.txt` file.

## Key Python Libraries & Modules

- **HTTP Requests:** `requests` - Used by `fetcher.py` to interact with the Yad2 API.
- **Telegram Integration:** `python-telegram-bot` - Used by `notifier.py` to send messages and notifications via the Telegram Bot API.
- **Environment Variables:** `python-dotenv` - Used by `config.py` to load configuration parameters from a `.env` file.
- **Asynchronous Operations:** `asyncio` - Employed in `main.py` and `notifier.py` to manage non-blocking operations, particularly for network calls and implementing delays to avoid rate-limiting.
- **Data Handling & Serialization:**
    - `json` (built-in): Used by `state.py` to read from and write to the `sent_listings.json` file, which stores the IDs and timestamps of processed listings.
    - `dataclasses` (built-in): Utilized in `dto.py` to define structured objects (`ApartmentDTO`, `AddressDTO`) for representing apartment listing data.
- **Logging:** `logging` (built-in) - Standard library used throughout the application for logging events and debugging information.
- **Command-Line Arguments:** `argparse` (built-in) - Used in `main.py` to parse command-line options (e.g., for a test mode).

## Development Setup & Execution

- **Running the Script:** The main entry point is `src/main.py`. It can be executed using `python -m src.main` from the project root.
- **Configuration:**
    - Managed via environment variables defined in a `.env` file located in the project root directory.
    - `src/config.py` is responsible for loading, parsing, and validating these variables.
    - Key variables include `YAD2_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BBOX_LIST`, and optional filter parameters like `MIN_PRICE`, `MAX_PRICE`, etc.
- **Dependencies:** Project dependencies are listed in `requirements.txt`.

## Scheduling

- The script is designed to be executed periodically to check for new listings. While `main.py` contains commented-out logic for an internal polling loop (`POLLING_INTERVAL_SECONDS`), the primary intended method for hourly execution is via an external system scheduler such as `cron` (Linux/macOS) or Task Scheduler (Windows), as per project requirements and `README.md`.

## Data Persistence

- **State File:** `sent_listings.json` is used to store the state of already processed/sent apartment listings. It maps listing IDs to timestamps (stored as ISO 8601 strings).
    - `src/state.py` handles loading this state, filtering new listings, and saving the updated state.

## Technical Constraints & Considerations

- **API Interaction (Yad2):**
    - The script scrapes the Yad2 API endpoint (`https://gw.yad2.co.il/realestate-feed/rent/map`).
    - Specific HTTP headers (e.g., `User-Agent`, `Referer`) are used in `fetcher.py` to mimic browser requests, likely to avoid detection or blocking.
    - The API is queried using geographic bounding boxes (`bBox` parameter), managed via the `BBOX_LIST` environment variable. A strategy for determining these boxes is outlined in `bounding_box_plan.md`.
    - Delays (`fetch_delay_seconds`) are implemented between consecutive API calls to Yad2 to act less aggressively.
- **Telegram API:**
    - Delays are implemented between sending individual Telegram notifications and certain operational messages (e.g., after "Search Initiated") to respect potential rate limits.
- **Error Handling:** Basic retry logic is present in `fetcher.py` for API calls. Logging is used to track errors and operational flow. 