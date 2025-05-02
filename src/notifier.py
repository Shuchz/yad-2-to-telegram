import logging
import telegram
from telegram import InputMediaPhoto
import asyncio
from typing import Optional, List

from .dto import ApartmentDTO, AddressDTO

logger = logging.getLogger(__name__)

def format_apartment_message(dto: ApartmentDTO) -> str:
    """Formats the apartment DTO into a more readable Markdown string."""
    lines = []
    # Use MarkdownV2 for better entity handling if needed, but requires escaping characters
    # For simplicity, stick to basic Markdown
    lines.append(f"*New Listing Found!* (ID: `{dto.id}`)")
    lines.append("------") # Separator

    # Combine address parts carefully
    if dto.address:
        addr_parts = []
        if dto.address.street:
            addr_parts.append(dto.address.street)
            if dto.address.number:
                addr_parts.append(dto.address.number)
        if dto.address.neighborhood:
            addr_parts.append(f"({dto.address.neighborhood})")
        if dto.address.city:
            addr_parts.append(dto.address.city)
        if addr_parts:
            lines.append(f"*Address:* { ' '.join(addr_parts) }")

    if dto.price:
        lines.append(f"*Price:* {dto.price}") # Already formatted with ₪
    if dto.rooms is not None:
        # Handle .0 display for whole numbers
        rooms_str = int(dto.rooms) if dto.rooms == int(dto.rooms) else dto.rooms
        lines.append(f"*Rooms:* {rooms_str}")
    if dto.floor is not None:
        lines.append(f"*Floor:* {dto.floor}")
    if dto.size is not None:
        lines.append(f"*Size:* {dto.size} sqm")

    if dto.description:
        # Limit description length
        desc = dto.description.strip()
        desc = desc[:250] + '...' if len(desc) > 250 else desc
        lines.append(f"\n*Description:*\n{desc}") # Add newline before description

    lines.append("------")

    if dto.updated_at:
        # Basic date formatting (can be improved with datetime parsing)
        lines.append(f"_Updated:_ `{dto.updated_at}`")

    # Link should always exist now
    lines.append(f"[Link to Yad2]({dto.link})")

    return '\n'.join(lines)

async def send_telegram_notification(token: str, chat_id: str, apartment: ApartmentDTO, parse_mode: str = 'Markdown') -> bool:
    """
    Sends a notification message about a listing to Telegram.
    Uses sendMediaGroup if 2-10 images are available, sendPhoto for 1 image,
    and sendMessage for 0 images.

    Args:
        token: The Telegram Bot API token.
        chat_id: The target Telegram chat ID.
        apartment: The ApartmentDTO object containing listing details.
        parse_mode: Telegram message parse mode for the caption/text.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    if not token or not chat_id:
        logger.error("Telegram token or chat_id is missing. Cannot send notification.")
        return False

    try:
        bot = telegram.Bot(token=token)
        message_text = format_apartment_message(apartment)
        image_urls: List[str] = apartment.image_urls
        num_images = len(image_urls)

        logger.info(f"Sending notification for apartment {apartment.id} to chat {chat_id} ({num_images} images)")

        if num_images == 0:
            # Send text message only
            await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode=parse_mode,
                disable_web_page_preview=False # Keep link preview
            )
            logger.debug(f"Sent text-only message for {apartment.id}.")

        elif num_images == 1:
            # Send single photo with caption
            await bot.send_photo(
                chat_id=chat_id,
                photo=image_urls[0],
                caption=message_text,
                parse_mode=parse_mode
            )
            logger.debug(f"Sent single photo message for {apartment.id}.")

        elif num_images >= 2:
            # Send media group (max 10 photos)
            media_group: List[InputMediaPhoto] = []
            limit = min(num_images, 10) # Telegram limit

            # Add first photo with caption
            media_group.append(InputMediaPhoto(media=image_urls[0], caption=message_text, parse_mode=parse_mode))

            # Add remaining photos (up to limit) without caption
            for i in range(1, limit):
                media_group.append(InputMediaPhoto(media=image_urls[i]))

            await bot.send_media_group(chat_id=chat_id, media=media_group)
            logger.debug(f"Sent media group ({limit} photos) for {apartment.id}.")
            if num_images > 10:
                logger.warning(f"Apartment {apartment.id} had {num_images} images, but only sent the first 10 due to Telegram limits.")

        logger.info(f"Successfully sent notification for apartment {apartment.id}")
        return True

    except telegram.error.BadRequest as e:
        logger.error(f"Telegram BadRequest Error sending notification for {apartment.id}: {e}", exc_info=True)
        if "can't parse entities" in str(e):
            logger.error("Potential Markdown formatting error in message. Consider sending as plain text or using HTML parse mode.")
        # Add other specific BadRequest checks if needed (e.g., URL issues for photos/media group)
        if "wrong type of the web page content" in str(e) or "failed to get HTTP URL content" in str(e):
             logger.error(f"Could not fetch one of the image URLs for {apartment.id}: {e}")
        return False
    except telegram.error.TimedOut:
        logger.warning(f"Telegram request timed out for apartment {apartment.id}. Will be retried next run if state saving failed or skipped.")
        return False
    except telegram.error.NetworkError as e:
         logger.warning(f"Telegram NetworkError sending notification for {apartment.id}: {e}. Potentially related to image URL.", exc_info=True)
         return False # Treat as failure for this attempt
    except telegram.error.RetryAfter as e:
        logger.warning(f"Telegram Flood control exceeded for {apartment.id}. Need to retry after {e.retry_after} seconds.")
        raise e
    except telegram.error.TelegramError as e:
        logger.error(f"Telegram API Error sending notification for {apartment.id}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram notification for {apartment.id}: {e}", exc_info=True)
        return False
