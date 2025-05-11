# MongoDB Integration Plan

This document outlines the plan to integrate MongoDB into the Yad2 Apartment Notifier project.

## Goal
To persist apartment data in a MongoDB database, allowing for more robust data storage, querying, and potential future analytics.

## URI
`mongodb+srv://apartment-searcher:L4k5S5M4tOXlsDCr@general.avqpi7g.mongodb.net/?retryWrites=true&w=majority&appName=General`
Collection Name: `apartments`

## Plan Phases

### Phase 1: Setup and Basic Connectivity

1.  **Create Repository Directory and File:**
    *   Create a new directory named `repositories` at the root of the project.
    *   Inside `repositories`, create a Python file named `mongo_repository.py`.
2.  **Install PyMongo:**
    *   Add `pymongo` to `requirements.txt`.
    *   Run `pip install pymongo` (or `pip install -r requirements.txt`).
3.  **MongoDB Connection URI Configuration:**
    *   Add the MongoDB connection URI to `.env` as `MONGO_URI`.
    *   Update `src/config.py` to load the `MONGO_URI`.
4.  **Implement Basic Connection in `mongo_repository.py`:**
    *   Import `MongoClient` from `pymongo`.
    *   Import `config` from `src.config`.
    *   `get_db_connection()`: Connects to MongoDB using `MONGO_URI`, returns database object (e.g., `client["apartment_data"]`).
    *   `get_apartments_collection()`: Calls `get_db_connection()`, returns the `apartments` collection object.
5.  **Initial Test (Recommended):**
    *   Add `if __name__ == "__main__":` block in `mongo_repository.py` for connection testing.

### Phase 2: Implement Core Functionalities

1.  **Write Function (`save_apartment`) in `mongo_repository.py`:**
    *   Input: `ApartmentDTO` object from `src.dto`.
    *   Action:
        *   Get `apartments` collection.
        *   Convert `ApartmentDTO` to a dictionary (handle `dataclasses.asdict`).
        *   Use `collection.insert_one()` or `collection.update_one({"id_": dto.id_}, {"$set": apartment_dict}, upsert=True)` to save/update.
        *   Implement error handling.
2.  **Read Function (`find_apartment_by_id`) in `mongo_repository.py`:**
    *   Input: `apartment_id: str`.
    *   Action:
        *   Get `apartments` collection.
        *   Use `collection.find_one({"id_": apartment_id})`.
        *   Return document or `None`.
3.  **Read All Function (`get_all_apartments` - Optional) in `mongo_repository.py`:**
    *   Action: Retrieve all documents from `apartments` collection.
    *   Return list of documents.

### Phase 3: Integrate with Existing Logic

1.  **Decision Point: Replace or Supplement `sent_listings.json`?**
    *   **Option A (Replace):**
        *   `load_sent_listings` in `src/state.py`: Query MongoDB for `id_`s.
        *   `save_sent_listings` in `src/state.py`: Call `mongo_repository.save_apartment`.
    *   **Option B (Supplement - Recommended for initial integration):**
        *   Keep `sent_listings.json` for primary "seen" logic.
        *   In `main.py`, after an apartment is processed and deemed new, call `mongo_repository.save_apartment`.
2.  **Update `main.py` (if using Option B or for testing):**
    *   Import functions from `repositories.mongo_repository`.
    *   Call `save_apartment` for new listings.

### Phase 4: Testing and Refinement

1.  **Testing:**
    *   Run the main script.
    *   Verify data saving in MongoDB "apartments" collection using a MongoDB client.
    *   Test read functionality.
2.  **Refinement:**
    *   Enhance error handling.
    *   Add logging for database operations.
    *   Review data types and consider MongoDB indexing (e.g., on `id_`).
    *   Update Memory Bank files (`techContext.md`, `systemPatterns.md`, `progress.md`) to reflect the MongoDB integration.
    *   Update `activeContext.md` to note this plan. 