#!/usr/bin/env python3
import json
import os
import logging
import time
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB Connection settings
DEFAULT_MONGO_URI = "mongodb+srv://apartment-searcher:L4k5S5M4tOXlsDCr@general.avqpi7g.mongodb.net/?retryWrites=true&w=majority&appName=General"

def get_mongo_uri():
    """Get MongoDB URI from env or use default"""
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()
    
    return os.getenv("MONGO_URI", DEFAULT_MONGO_URI)

def string_to_numeric_id(apt_id):
    """
    Convert string apartment ID to numeric ID for MongoDB _id field
    
    We'll use a simple approach: extract numeric parts and convert to int
    If not possible, use a hash function to convert to a number
    """
    # Try to extract numeric part
    numeric_part = ''.join(filter(str.isdigit, apt_id))
    if numeric_part:
        return int(numeric_part)
    
    # Fallback to hash if no numeric part
    return hash(apt_id) & 0x7FFFFFFF  # Ensure positive number

def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to datetime object"""
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp)
    # If timestamp is a string, try to parse it
    try:
        return datetime.fromtimestamp(float(timestamp))
    except (ValueError, TypeError):
        # Default to current time if parsing fails
        logger.warning(f"Failed to parse timestamp {timestamp}, using current time")
        return datetime.now()

def migrate_sent_listings():
    """Migrate sent_listings.json to MongoDB collection with _id and seen_at as datetime"""
    try:
        # Connect to MongoDB
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        # Clear existing collection to avoid duplicates
        collection.delete_many({})
        logger.info("Cleared existing seen_apartments collection")
        
        # Read existing sent_listings.json
        with open('sent_listings.json', 'r') as f:
            sent_listings = json.load(f)
        
        if not sent_listings:
            logger.error("No listings found in sent_listings.json")
            return False
        
        # Create list of minimal documents
        docs_to_insert = []
        for apt_id, timestamp in sent_listings.items():
            numeric_id = string_to_numeric_id(apt_id)
            datetime_obj = timestamp_to_datetime(timestamp)
            
            docs_to_insert.append({
                "_id": numeric_id,
                "seen_at": datetime_obj
            })
        
        # Use bulk write for better performance
        if docs_to_insert:
            # Insert in batches of 1000 for better performance with large datasets
            batch_size = 1000
            for i in range(0, len(docs_to_insert), batch_size):
                batch = docs_to_insert[i:i + batch_size]
                try:
                    result = collection.insert_many(batch, ordered=False)
                    logger.info(f"Inserted batch {i//batch_size + 1} with {len(result.inserted_ids)} documents")
                except Exception as e:
                    # Continue if some documents fail (duplicate _id)
                    logger.warning(f"Error in batch {i//batch_size + 1}: {e}")
        
        # Final count
        total_count = collection.count_documents({})
        logger.info(f"Migration complete. Total documents in seen_apartments collection: {total_count}")
        logger.info(f"Original sent_listings.json had {len(sent_listings)} entries")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

def add_seen_apartment(apt_id):
    """Add a new apartment ID to the seen_apartments collection"""
    try:
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        numeric_id = string_to_numeric_id(apt_id)
        current_time = datetime.now()
        
        # Use upsert to avoid duplicate key errors
        result = collection.update_one(
            {"_id": numeric_id},
            {"$set": {
                "seen_at": current_time
            }},
            upsert=True
        )
        
        logger.info(f"Added/updated apartment with ID: {apt_id}, numeric ID: {numeric_id}, time: {current_time}")
        return True
    except Exception as e:
        logger.error(f"Error adding apartment {apt_id} to seen_apartments: {e}")
        return False

def is_apartment_seen(apt_id):
    """Check if apartment ID exists in seen_apartments collection by numeric ID"""
    try:
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        # Convert to numeric ID and check by _id
        numeric_id = string_to_numeric_id(apt_id)
        return collection.find_one({"_id": numeric_id}) is not None
    except Exception as e:
        logger.error(f"Error checking if apartment {apt_id} is seen: {e}")
        return False

def get_all_seen_apartments():
    """Get all seen apartment IDs and timestamps"""
    try:
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        return list(collection.find({}))
    except Exception as e:
        logger.error(f"Error getting all seen apartments: {e}")
        return []

def lookup_by_numeric_id(apt_id):
    """Lookup an apartment by converting string ID to numeric ID"""
    try:
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        numeric_id = string_to_numeric_id(apt_id)
        result = collection.find_one({"_id": numeric_id})
        return result
    except Exception as e:
        logger.error(f"Error looking up by numeric ID for {apt_id}: {e}")
        return None

def get_all_seen_apartment_ids():
    """Get all seen apartment ids as a set for efficient in-memory checking"""
    try:
        client = MongoClient(get_mongo_uri(), tlsAllowInvalidCertificates=True)
        db = client["apartment_data"]
        collection = db["seen_apartments"]
        
        # Get only the _id field for efficiency
        ids_cursor = collection.find({}, {"_id": 1})
        
        # Convert to set of numeric IDs
        seen_ids = {doc["_id"] for doc in ids_cursor}
        
        logger.info(f"Retrieved {len(seen_ids)} seen apartment IDs from MongoDB")
        return seen_ids
    except Exception as e:
        logger.error(f"Error getting seen apartment IDs from MongoDB: {e}")
        return set()

if __name__ == "__main__":
    logger.info("Starting sent_listings.json migration to MongoDB")
    if migrate_sent_listings():
        logger.info("Migration successful")
        
        # Test the new functions
        test_id = "test_migration_" + str(int(time.time()))
        logger.info(f"Testing with ID: {test_id}")
        
        # Check if exists (should be False)
        logger.info(f"Is {test_id} seen before adding: {is_apartment_seen(test_id)}")
        
        # Add test ID
        add_seen_apartment(test_id)
        logger.info(f"Added {test_id} to seen_apartments")
        
        # Check if exists (should be True)
        logger.info(f"Is {test_id} seen after adding: {is_apartment_seen(test_id)}")
        
        # Get the record by numeric ID
        record = lookup_by_numeric_id(test_id)
        if record:
            logger.info(f"Found record - _id: {record['_id']}, seen_at: {record['seen_at']}")
        
        # Count total
        seen_apts = get_all_seen_apartments()
        logger.info(f"Total seen apartments: {len(seen_apts)}")
    else:
        logger.error("Migration failed") 