#!/usr/bin/env python3
import json
import logging
from src.dto import ApartmentDTO, AddressDTO
from repositories.mongo_repository import save_apartment, get_all_apartments

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_apartment():
    # Create a test apartment DTO
    address = AddressDTO(
        city="Tel Aviv",
        street="Dizengoff",
        number="50",
        neighborhood="Lev Hair"
    )
    
    apartment = ApartmentDTO(
        id="test123456",
        price=5000,
        rooms=3,
        floor=3,
        size=80,
        description="Beautiful Apartment in Tel Aviv",
        image_urls=["https://img.yad2.co.il/Pic/202311/05/1_1/o/test123456_1.jpg"],
        address=address,
        neighborhood_id=1461,
        link="https://www.yad2.co.il/item/test123456",
        updated_at="2023-11-05"
    )
    
    return apartment

def add_existing_apartment_from_json():
    """
    Load an existing apartment from sent_listings.json and save it to MongoDB
    """
    # Load sent_listings.json
    try:
        with open('sent_listings.json', 'r') as f:
            sent_listings = json.load(f)
            
        if not sent_listings:
            logger.error("No listings found in sent_listings.json")
            return None
            
        # Get a listing ID from sent_listings
        listing_id = next(iter(sent_listings.keys()))
        
        # Create a sample apartment with that ID
        apartment = ApartmentDTO(
            id=listing_id,
            price=6000,
            rooms=2.5,
            floor=2,
            size=65,
            description=f"Apartment {listing_id}",
            image_urls=[f"https://img.yad2.co.il/Pic/202311/05/1_1/o/{listing_id}_1.jpg"],
            address=AddressDTO(
                city="Tel Aviv",
                street="Rothschild",
                number="10",
                neighborhood="Neve Tzedek"
            ),
            neighborhood_id=1520,
            link=f"https://www.yad2.co.il/item/{listing_id}",
            updated_at="2023-11-05"
        )
        
        return apartment
    except Exception as e:
        logger.error(f"Error loading apartment from sent_listings.json: {e}")
        return None

def main():
    # Option 1: Create a test apartment
    test_apartment = create_test_apartment()
    logger.info(f"Created test apartment with ID: {test_apartment.id}")
    
    # Option 2: Use an existing apartment ID from sent_listings.json
    existing_apartment = add_existing_apartment_from_json()
    if existing_apartment:
        logger.info(f"Loaded existing apartment with ID: {existing_apartment.id}")
        
        # Save the apartment to MongoDB
        save_apartment(existing_apartment)
        logger.info(f"Saved apartment with ID {existing_apartment.id} to MongoDB")
    
    # Save the test apartment to MongoDB
    save_apartment(test_apartment)
    logger.info(f"Saved test apartment with ID {test_apartment.id} to MongoDB")
    
    # Check how many apartments are in the database
    apartments = get_all_apartments()
    logger.info(f"Total apartments in MongoDB: {len(apartments)}")
    
if __name__ == '__main__':
    main() 