import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# --- Helper Function --- #
def _safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Safely access nested dictionary keys."""
    temp = data
    for key in keys:
        if isinstance(temp, dict):
            temp = temp.get(key)
        else:
            return default
        if temp is None:
            return default
    return temp

# --- DTO Classes --- #
@dataclass
class AddressDTO:
    """Data Transfer Object for address information."""
    city: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None # Often missing or requires different parsing
    neighborhood: Optional[str] = None

    @classmethod
    def from_api_data(cls, address_data: Optional[Dict[str, Any]]) -> Optional['AddressDTO']:
        """Creates an AddressDTO from the 'address' part of a listing."""
        if not address_data or not isinstance(address_data, dict):
            return None

        # Extract data using helper for nested access
        city = _safe_get_nested(address_data, ['city', 'text'])
        street = _safe_get_nested(address_data, ['street', 'text'])
        neighborhood = _safe_get_nested(address_data, ['neighborhood', 'text'])
        # House number is sometimes directly in address_data, sometimes nested in house
        number_raw = address_data.get('house_number') or _safe_get_nested(address_data, ['house', 'number'])
        number = str(number_raw) if number_raw else None

        return cls(
            city=city,
            street=street,
            number=number,
            neighborhood=neighborhood
        )

@dataclass
class ApartmentDTO:
    """Data Transfer Object for an apartment listing."""
    id: str # Use adNumber as the unique identifier
    price: Optional[int] = None # Changed to Optional[int]
    rooms: Optional[float] = None
    floor: Optional[int] = None # Extracted as int
    size: Optional[int] = None # Square meters
    description: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    address: Optional[AddressDTO] = None
    neighborhood_id: Optional[int] = None # Added neighborhood ID
    # Contact info seems unavailable directly
    # contact_name: Optional[str] = None
    # contact_phone: Optional[str] = None
    link: Optional[str] = None # Constructed link
    updated_at: Optional[str] = None # Added field

    @classmethod
    def from_api_data(cls, item_data: Dict[str, Any]) -> Optional['ApartmentDTO']:
        """
        Parses raw API item data dictionary (from a marker) into an ApartmentDTO.
        Args: item_data: Dictionary representing a single marker.
        Returns: An ApartmentDTO instance or None if parsing fails.
        """
        if not item_data or not isinstance(item_data, dict):
            logger.warning("Invalid item data (marker) received: not a dictionary or empty.")
            return None

        try:
            # --- Core Identifier (Using orderId from marker) --- #
            listing_id = item_data.get('orderId')
            if not listing_id:
                logger.warning(f"Missing essential 'orderId' field in marker data: {item_data.get('token', 'Unknown Token')}")
                return None
            listing_id_str = str(listing_id)

            # --- Basic & Nested Fields (from marker structure) --- #
            price_raw = item_data.get('price')
            rooms_raw = _safe_get_nested(item_data, ['additionalDetails', 'roomsCount'])
            floor_raw = _safe_get_nested(item_data, ['address', 'house', 'floor'])
            size_raw = _safe_get_nested(item_data, ['additionalDetails', 'squareMeter'])
            # --- Fields likely missing in markers --- #
            description = None # Not available in markers
            # --- Get image list from metaData.images --- # Corrected logic
            images_list_raw = _safe_get_nested(item_data, ['metaData', 'images'], default=[])
            # --- End image list extraction --- #
            updated_at = None # Not available in markers
            neighborhood_id_raw = None # Not available in markers
            # --- End missing fields --- #

            address_dict = item_data.get('address')

            # --- Data Cleaning & Type Conversion --- #
            price = None
            try:
                if price_raw is not None:
                    cleaned_price_raw = ''.join(filter(str.isdigit, str(price_raw)))
                    if cleaned_price_raw:
                         price = int(cleaned_price_raw)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert price '{price_raw}' to int for marker {listing_id_str}.")

            rooms = None
            try:
                if rooms_raw is not None:
                    rooms = float(rooms_raw)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert rooms '{rooms_raw}' to float for marker {listing_id_str}.")

            floor = None
            try:
                if floor_raw is not None:
                    floor = int(floor_raw)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert floor '{floor_raw}' to int for marker {listing_id_str}.")

            size = None
            try:
                if size_raw is not None:
                    size = int(size_raw)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert size '{size_raw}' to int for marker {listing_id_str}.")

            neighborhood_id = None # Remains None as not available in marker

            # Process the extracted images list
            image_urls = [str(img) for img in images_list_raw if isinstance(img, str)] if isinstance(images_list_raw, list) else []

            # --- Nested DTO --- #
            address_dto = AddressDTO.from_api_data(address_dict)

            # --- Constructed Fields --- #
            # Use the 'token' field for the direct item link if available
            token = item_data.get('token')
            if token:
                link = f"https://www.yad2.co.il/realestate/item/{token}"
            else:
                logger.warning(f"Missing 'token' field for marker {listing_id_str}. Using fallback map link.")
                # Fallback link construction using coordinates
                lat = _safe_get_nested(address_dict, ['coords', 'lat'])
                lon = _safe_get_nested(address_dict, ['coords', 'lon'])
                link = f"https://www.yad2.co.il/realestate/rent?lat={lat}&lng={lon}&zoom=15" if lat and lon else "https://www.yad2.co.il/realestate/rent" # Generic fallback

            # --- Create DTO Instance --- #
            return cls(
                id=listing_id_str,
                price=price,
                rooms=rooms,
                floor=floor,
                size=size,
                description=description, # Will be None
                image_urls=image_urls,   # Use the properly parsed list from metaData.images
                address=address_dto,
                neighborhood_id=neighborhood_id, # Will be None
                link=link,               # Updated link construction
                updated_at=updated_at    # Will be None
            )

        except Exception as e:
            logger.error(f"Failed to parse marker data for listing ID {item_data.get('orderId', 'UNKNOWN')}. Error: {e}", exc_info=True)
            return None

# Example Helper function (can be outside class or static method)
def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely gets a value from a dictionary."""
    return data.get(key, default)

# Add more helper functions for type conversions as needed, e.g., parse_date, parse_bool
