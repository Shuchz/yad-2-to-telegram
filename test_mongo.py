#!/usr/bin/env python3
import time
import logging
from src.dto import ApartmentDTO
from repositories.mongo_repository import save_apartment
from migrate_sent_listings import add_seen_apartment, is_apartment_seen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Generate unique test ID
    test_id = f'test_{int(time.time())}'
    logger.info(f'Testing with ID: {test_id}')
    
    # Check if apartment exists before adding
    seen_before = is_apartment_seen(test_id)
    logger.info(f'Apartment seen before test: {seen_before}')
    
    # Create test apartment
    apt = ApartmentDTO(id=test_id)
    
    # Add to both collections
    try:
        # Add to seen_apartments collection (via migrate_sent_listings.py)
        add_seen_apartment(test_id)
        logger.info("Successfully added to seen_apartments collection")
        
        # Add to apartments collection (via mongo_repository.py)
        save_apartment(apt)
        logger.info("Successfully added to apartments collection")
        
        # Check if apartment exists after adding
        seen_after = is_apartment_seen(test_id)
        logger.info(f'Apartment seen after test: {seen_after}')
        
        if seen_after:
            logger.info("Success: Both MongoDB collections work together")
        else:
            logger.error("Error: Apartment not found after adding")
    except Exception as e:
        logger.error(f'Error during test: {e}')

if __name__ == "__main__":
    main() 