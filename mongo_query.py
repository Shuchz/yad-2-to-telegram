#!/usr/bin/env python3
import logging
from repositories.mongo_repository import find_apartment_by_id, get_all_apartments

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get all apartments
    apartments = get_all_apartments()
    logger.info(f"Total apartments in MongoDB: {len(apartments)}")
    
    # List all apartments
    for i, apt in enumerate(apartments):
        logger.info(f"Apartment {i+1}: ID={apt['id']}, Price={apt.get('price')}, Link={apt.get('link')}")
    
    # Find a specific apartment by ID
    apartment_id = "test123456"
    apartment = find_apartment_by_id(apartment_id)
    
    if apartment:
        logger.info(f"Found apartment with ID: {apartment['id']}")
        logger.info(f"Price: {apartment.get('price')}")
        logger.info(f"Rooms: {apartment.get('rooms')}")
        logger.info(f"Size: {apartment.get('size')}")
        
        address = apartment.get('address')
        if address:
            logger.info(f"Address: {address.get('street')} {address.get('number')}, {address.get('neighborhood')}, {address.get('city')}")
    else:
        logger.warning(f"No apartment found with ID: {apartment_id}")

if __name__ == '__main__':
    main() 