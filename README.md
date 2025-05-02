# Yad2 Apartment Notifier

This script monitors a Yad2 apartment search URL for new listings and sends notifications via Telegram.

## Features

- Fetches apartment listings from a specified Yad2 URL.
- Parses relevant details (price, rooms, address, images, etc.).
- Keeps track of listings already sent to avoid duplicate notifications.
- **Filters listings based on price and neighborhood:** Currently configured to only notify about apartments with a price less than ₪8000 and located in specific neighborhoods (IDs: 1520, 1461, 205).
- Sends notifications for new, matching listings to a specified Telegram chat via a bot.
- Includes basic error handling and logging.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd apartment-search
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    - Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file and fill in your details:
      - `YAD2_URL`: The URL from your Yad2 search results page. Make sure it includes the filters you want _before_ the script's filtering.
      - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token obtained from BotFather.
      - `TELEGRAM_CHAT_ID`: The ID of the chat where the bot should send notifications. You can get this from bots like `@userinfobot`.

## Usage

Run the main script from the project root directory:

```bash
python -m src.main
```

The script will perform one check, send notifications for any new listings that match the criteria, and then exit. You can set this up to run periodically using tools like `cron` (Linux/macOS) or Task Scheduler (Windows).

## Configuration

- **Search URL & Telegram:** Configured via the `.env` file.
- **Filtering Criteria (Price & Neighborhood):** Currently hardcoded within `src/main.py`. Look for the `MAX_PRICE` and `ALLOWED_NEIGHBORHOODS` variables inside the `run_check` function if you need to modify them.
- **Polling Interval (for continuous run):** If you modify `src/main.py` to run continuously (see commented-out code), the interval is set by `POLLING_INTERVAL_SECONDS`.
- **State File:** Sent listing IDs are stored in `sent_listings.json` in the project root by default.
