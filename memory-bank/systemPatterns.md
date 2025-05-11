# System Patterns

## System Architecture Overview

The Yad2 Apartment Notifier is a Python-based script designed to automate the process of finding and reporting new apartment listings. It operates as a sequence of data processing stages, orchestrated by a main script (`main.py`). The architecture emphasizes modularity, with distinct components responsible for specific tasks such as fetching data, parsing it, managing state, and sending notifications.

## Component Breakdown and Relationships

The system comprises the following core components, primarily located within the `src/` directory:

1.  **`main.py` (Orchestrator):**
    *   The central control flow module.
    *   Initializes and loads configuration (`config.py`).
    *   Manages the overall process: fetch -> parse -> filter (state) -> notify.
    *   Handles command-line arguments (e.g., for test mode).
    *   Initiates logging.

2.  **`config.py` (Configuration Manager):**
    *   Loads settings from environment variables (via a `.env` file using `python-dotenv`).
    *   Provides typed configuration values (e.g., API URLs, tokens, filter criteria) to other modules.

3.  **`fetcher.py` (Data Retriever):**
    *   Responsible for making HTTP GET requests to the Yad2 API endpoint.
    *   Uses the `requests` library.
    *   Implements retry logic and custom headers to mimic browser behavior and handle potential network issues.
    *   Receives API parameters (including bounding boxes) from `main.py`.
    *   Returns the raw JSON response from the API.

4.  **`dto.py` (Data Transfer Objects):**
    *   Defines structured representations of apartment data (`ApartmentDTO`, `AddressDTO`) using Python's `dataclasses`.
    *   Includes class methods (`from_api_data`) to parse raw dictionary data (from individual API items) into these DTO instances, ensuring type safety and consistent data access.

5.  **`listing_parser.py` (Data Transformer):**
    *   Takes the raw JSON data (specifically, the list of listing markers) from `fetcher.py`.
    *   Iterates through each listing item and uses `ApartmentDTO.from_api_data()` to convert it into a structured `ApartmentDTO` object.
    *   Returns a list of `ApartmentDTO` objects.

6.  **`state.py` (State Manager):**
    *   Manages the persistence of seen apartment listings to prevent duplicate notifications.
    *   Loads listing IDs and their first-seen timestamps from `sent_listings.json`.
    *   Provides a function to filter a list of `ApartmentDTOs` against the loaded state, returning only new listings.
    *   Saves the updated state (with new listings and their timestamps) back to `sent_listings.json` (timestamps stored as ISO 8601 strings).

7.  **`notifier.py` (Notification Sender):**
    *   Formats information from an `ApartmentDTO` into a human-readable message (Markdown).
    *   Uses the `python-telegram-bot` library to send these messages, potentially including images, to a configured Telegram chat via a bot.
    *   Handles Telegram API specific logic, including sending messages, photos, and media groups.
    *   Implements delays and handles `RetryAfter` exceptions from Telegram.

**Data Flow (Simplified):**
`main.py` -> `config.py` (load settings)
`main.py` -> `fetcher.py` (get raw data using multiple bounding boxes)
`fetcher.py` -> `main.py` (return raw data)
`main.py` -> `listing_parser.py` (parse raw data)
`listing_parser.py` (uses `dto.py`) -> `main.py` (return list of `ApartmentDTO`s)
`main.py` -> `state.py` (load sent listings, filter new ones)
`state.py` -> `main.py` (return list of new `ApartmentDTO`s)
`main.py` -> `notifier.py` (send notifications for new DTOs)
`notifier.py` -> Telegram API
`main.py` -> `state.py` (save updated sent listings state)

The relationship is also visually represented in `architecture.txt` using a Mermaid diagram.

## Key Technical Decisions & Design Patterns

- **Modularity:** The system is broken down into single-responsibility modules (fetch, parse, notify, state, config), promoting separation of concerns and maintainability.
- **Configuration over Hardcoding:** Critical parameters (API keys, URLs, chat IDs, filter criteria) are managed through environment variables (`.env` file and `config.py`) rather than being hardcoded directly in the logic, allowing for easier modification without code changes.
- **Data Transfer Objects (DTOs):** `dto.py` uses `dataclasses` to define clear, structured objects for apartment data. This improves code readability, type safety, and decouples the internal data representation from the raw API response structure.
- **Stateful Processing:** The application maintains state (`sent_listings.json`) to track processed listings and avoid sending duplicate notifications. Timestamps are stored with IDs for potential future analysis or more complex filtering.
- **Asynchronous Operations for I/O:** `asyncio` is used for network-bound operations (Telegram notifications and delays) in `main.py` and `notifier.py` to prevent blocking the entire script, especially when dealing with multiple notifications or imposed delays.
- **Bounding Box Strategy for API Queries:** Instead of relying on potentially imprecise neighborhood ID filters alone, the system uses a list of geographic bounding boxes (`BBOX_LIST`) to query the Yad2 API. This decision, planned in `bounding_box_plan.md`, aims for more precise geographic targeting by making multiple, focused API calls and aggregating the results.
- **External Scheduling:** The script is primarily designed for periodic execution (e.g., hourly) via an external scheduler like `cron`, rather than implementing a long-running internal loop by default. This simplifies the script's own process management.
- **Error Handling and Resilience:**
    - `fetcher.py` includes basic retry mechanisms for API calls.
    - `notifier.py` handles specific Telegram API errors, including rate limiting (`RetryAfter`).
    - Logging is implemented throughout to aid in debugging and monitoring.
- **Stealth and API Etiquette:**
    - Custom User-Agent and other HTTP headers are used in `fetcher.py`.
    - Delays are introduced between API calls (`fetch_delay_seconds`) and Telegram notifications (`asyncio.sleep`) to reduce the load on external services and minimize the risk of being rate-limited or blocked. 