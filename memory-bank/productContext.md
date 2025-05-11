# Product Context

## Why This Project Exists

This project was created to address the significant challenge of finding available apartments in Tel Aviv. The highly competitive and fast-moving nature of the Tel Aviv rental market makes manual searching inefficient and often frustrating.

## Problems It Solves

- **Reduces Manual Effort:** Automates the time-consuming task of repeatedly checking websites for new apartment listings.
- **Overcomes Market Speed:** Provides timely updates, increasing the chances of seeing and responding to new listings quickly before they are gone.
- **Filters Noise:** By remembering previously seen listings, it ensures that the user only sees new opportunities, saving time and effort.

## How It Should Work

The system operates as an automated agent:
1.  **Scheduled Execution:** It runs automatically every hour, similar to a cron job.
2.  **Targeted Scraping:** It focuses on specific apartment listing websites (e.g., Yad2) to gather data.
3.  **Intelligent Filtering:** It processes the scraped listings, identifies new ones, and discards those already seen by the user.
4.  **Direct Notification:** New and relevant listings are sent directly to the user via Telegram, providing immediate access to the information.

## User Experience Goals

- **Timeliness:** Users should receive notifications for new apartments as soon as possible after they are listed.
- **Relevance:** Notifications should only contain new, unique listings that match the user's implicit interest (apartments in Tel Aviv).
- **Convenience:** The information should be delivered directly to a commonly used platform (Telegram) in a clear and concise format, allowing for quick review and action.
- **Effortless:** The system should operate autonomously in the background, requiring minimal user intervention after initial setup. 