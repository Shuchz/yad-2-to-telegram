from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import os
from dotenv import load_dotenv
from src.dto import ApartmentDTO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Connection URI (fallback if config not loaded)
DEFAULT_MONGO_URI = "mongodb+srv://apartment-searcher:L4k5S5M4tOXlsDCr@general.avqpi7g.mongodb.net/?retryWrites=true&w=majority&appName=General"

def get_mongo_uri() -> str:
    """
    Gets the MongoDB URI from environment variables or uses the default.
    
    Returns:
        str: MongoDB connection URI
    """
    # Try to load from .env first
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()
    
    # Get MONGO_URI from environment, or use default
    return os.getenv("MONGO_URI", DEFAULT_MONGO_URI)

def get_db_connection() -> Database:
    """
    Establishes a connection to MongoDB and returns the database object.
    
    Returns:
        Database: MongoDB database object
    """
    mongo_uri = get_mongo_uri()
    
    try:
        # Add tlsAllowInvalidCertificates=true to bypass SSL certificate verification
        client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
        # Use "apartment_data" as the database name
        db = client["apartment_data"]
        logger.info("MongoDB connection established successfully")
        return db
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

def get_apartments_collection() -> Collection:
    """
    Returns the 'apartments' collection from the MongoDB database.
    
    Returns:
        Collection: MongoDB collection object for apartments
    """
    db = get_db_connection()
    return db["apartments"]

def save_apartment(dto: ApartmentDTO) -> str:
    """
    Saves an ApartmentDTO to the MongoDB apartments collection.
    If an apartment with the same id already exists, it will be updated.
    
    Args:
        dto (ApartmentDTO): The apartment data to save
        
    Returns:
        str: The MongoDB document ID of the inserted/updated document
    """
    try:
        collection = get_apartments_collection()
        
        # Convert ApartmentDTO to dictionary (excluding None values)
        apartment_dict = {
            "id": dto.id,
            "price": dto.price,
            "rooms": dto.rooms,
            "floor": dto.floor,
            "size": dto.size,
            "description": dto.description,
            "image_urls": dto.image_urls,
            "neighborhood_id": dto.neighborhood_id,
            "link": dto.link,
            "updated_at": dto.updated_at
        }
        
        # Add address details if available
        if dto.address:
            apartment_dict["address"] = {
                "city": dto.address.city,
                "street": dto.address.street,
                "number": dto.address.number,
                "neighborhood": dto.address.neighborhood
            }
        
        # Remove None values
        apartment_dict = {k: v for k, v in apartment_dict.items() if v is not None}
        
        # Upsert the document based on the id field
        result = collection.update_one(
            {"id": dto.id},
            {"$set": apartment_dict},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"Inserted new apartment with ID: {dto.id}")
            return str(result.upserted_id)
        else:
            logger.info(f"Updated existing apartment with ID: {dto.id}")
            return dto.id
    
    except Exception as e:
        logger.error(f"Error saving apartment to MongoDB: {e}")
        raise

def find_apartment_by_id(apartment_id: str):
    """
    Retrieves an apartment document by its Yad2 ID.
    
    Args:
        apartment_id (str): The Yad2 ID of the apartment
        
    Returns:
        dict or None: The apartment document if found, None otherwise
    """
    try:
        collection = get_apartments_collection()
        return collection.find_one({"id": apartment_id})
    except Exception as e:
        logger.error(f"Error finding apartment in MongoDB: {e}")
        raise

def get_all_apartments():
    """
    Retrieves all apartment documents from the MongoDB collection.
    
    Returns:
        list: A list of all apartment documents
    """
    try:
        collection = get_apartments_collection()
        return list(collection.find())
    except Exception as e:
        logger.error(f"Error retrieving apartments from MongoDB: {e}")
        raise

# Test the MongoDB connection if this file is run directly
if __name__ == "__main__":
    try:
        db = get_db_connection()
        collection = get_apartments_collection()
        logger.info(f"Successfully connected to database: {db.name}")
        logger.info(f"Apartments collection: {collection.name}")
        logger.info(f"Document count: {collection.count_documents({})}")
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}") 