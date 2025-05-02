import requests # Re-add requests as it's generally easier than urllib
import json
from collections import deque
import time

# --- Configuration ---
# Reset to larger initial box and broader filters for automated search
initial_bbox = "32.02,34.74,32.12,34.84"
target_neighborhoods = {1461, 1520, 205}
api_base_url = "https://gw.yad2.co.il/realestate-feed/rent/map"

# Keep broader params for exploration
other_params = {
    "minPrice": 1000,
    "maxPrice": 25000,
    # "minRooms": 2,
    # "maxRooms": 5,
    # Include zoom and multiNeighborhood if they proved necessary, 
    # but try without first for wider exploration, add back if needed.
    # "multiNeighborhood": ",".join(map(str, target_neighborhoods)),
    # "zoom": 15
}

# Stop subdividing if box dimensions are smaller than this
MIN_LAT_DIFF = 0.001
MIN_LON_DIFF = 0.001

# Delay between API calls
REQUEST_DELAY_SECONDS = 0.5

# Use the detailed headers that seemed necessary
request_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.yad2.co.il',
    'Referer': 'https://www.yad2.co.il/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
}
# --- End Configuration ---

# --- Helper Functions ---
def parse_bbox(bbox_str):
    """Parse bbox string into float coordinates."""
    try:
        parts = list(map(float, bbox_str.split(',')))
        if len(parts) == 4:
            return parts[0], parts[1], parts[2], parts[3]
    except ValueError:
        pass
    print(f"Error parsing bbox string: {bbox_str}")
    return None

def is_contained(inner_bbox_str, outer_bbox_str):
    """Check if inner_bbox is geographically contained within outer_bbox."""
    inner = parse_bbox(inner_bbox_str)
    outer = parse_bbox(outer_bbox_str)
    if inner and outer:
        lat_min_in, lon_min_in, lat_max_in, lon_max_in = inner
        lat_min_out, lon_min_out, lat_max_out, lon_max_out = outer
        return (
            lat_min_in >= lat_min_out and
            lon_min_in >= lon_min_out and
            lat_max_in <= lat_max_out and
            lon_max_in <= lon_max_out
        )
    return False
# --- End Helper Functions ---

def fetch_neighborhoods(bbox_str):
    """Fetches listings using requests and parses the 'data.markers' structure."""
    print(f"--- Testing Bounding Box: {bbox_str} ---", end='')
    coords = parse_bbox(bbox_str)
    if not coords:
        print(" Invalid format.")
        return set()

    lat_min, lon_min, lat_max, lon_max = coords
    if (lat_max - lat_min) < MIN_LAT_DIFF or (lon_max - lon_min) < MIN_LON_DIFF:
        print(" Box too small, skipping.")
        return set()

    params = other_params.copy()
    params["bBox"] = bbox_str

    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        response = requests.get(api_base_url, params=params, headers=request_headers, timeout=10)
        # print(f"\nRequest URL: {response.url}") # Uncomment to debug the exact URL
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        found_neighborhoods = set()
        item_count = 0
        # --- MODIFIED PARSING LOGIC --- 
        if "data" in data and "markers" in data["data"]:
            items = data["data"]["markers"] # Look in data.markers
            item_count = len(items)
            for item in items:
                # Neighborhood ID seems to be nested within address in this structure
                if "address" in item and isinstance(item["address"], dict) and "neighborhood" in item["address"] and isinstance(item["address"]["neighborhood"], dict) and "text" in item["address"]["neighborhood"]:
                    # The ID is not directly available in the example, need to infer based on cluster data or potentially another field if available.
                    # For now, let's try extracting the ID from the cluster data if present.
                    # This is an assumption based on common API patterns.
                    # If there's a direct neighborhood ID field in the marker, use that.
                    # Example: Check if item['neighborhood_id'] exists.
                    # Fallback: We might need to map the neighborhood *name* (item["address"]["neighborhood"]["text"]) back to an ID if no direct ID is present.
                    # TEMPORARY: Let's just print the neighborhood name found for now to see what we get.
                    neighborhood_name = item["address"]["neighborhood"]["text"]
                    # We need a reliable way to get the *ID* here.
                    # Placeholder: Assume we extract ID somehow, e.g., from a hypothetical item['neighborhood_id']
                    if "neighborhood_id" in item: # Check for a direct ID field (replace 'neighborhood_id' with actual key if found)
                        try:
                           found_neighborhoods.add(int(item["neighborhood_id"]))
                        except (ValueError, TypeError):
                           pass # Ignore if not an integer ID
                    # else: print(f" (Found neighborhood name: {neighborhood_name})", end='') # Debug: print name if no ID
                # If the structure is different, adjust the path above accordingly.

        # Also check the `clusters` array, as it contains IDs
        if "data" in data and "clusters" in data["data"]:
            clusters = data["data"]["clusters"]
            for cluster in clusters:
                if "key" in cluster:
                    try:
                        # Assume cluster 'key' is the neighborhood ID
                        found_neighborhoods.add(int(cluster["key"]))
                    except (ValueError, TypeError):
                        pass # Ignore if not an integer ID
        # --- END MODIFIED PARSING LOGIC --- 
        
        # We need to refine item_count based on actual listings found if possible, 
        # for now, it might just count markers/clusters found in the response.
        # Let's report based on unique neighborhoods found in the set.
        print(f" Found {len(found_neighborhoods)} unique neighborhood IDs (from markers/clusters). Neighborhoods: {found_neighborhoods or 'None'}")
        return found_neighborhoods

    except requests.exceptions.RequestException as e:
        print(f" Error during API request: {e}")
        return set()
    except json.JSONDecodeError as e:
        print(f" Error decoding JSON: {e}")
        try:
            print(f" Raw response text (first 500): {response.text[:500]}")
        except NameError:
            pass # response object might not exist
        return set()

if __name__ == "__main__":
    # Restore automated search logic
    print("Starting Automated Bounding Box Analysis (using requests, parsing data.markers/clusters)...")
    print(f"Target Neighborhood IDs: {target_neighborhoods}")

    boxes_to_check = deque([initial_bbox])
    checked_boxes = set()
    candidate_boxes = {}
    all_found_targets = set()
    checked_count = 0 # Counter for progress indicator

    while boxes_to_check:
        current_bbox = boxes_to_check.popleft()

        if current_bbox in checked_boxes:
            continue
        
        checked_count += 1
        checked_boxes.add(current_bbox)

        # Print progress periodically
        if checked_count % 20 == 0:
            print(f"\n[Progress] Queue size: {len(boxes_to_check)}, Checked boxes: {checked_count}...")

        coords = parse_bbox(current_bbox)
        if not coords:
            continue

        lat_min, lon_min, lat_max, lon_max = coords
        if (lat_max - lat_min) < MIN_LAT_DIFF or (lon_max - lon_min) < MIN_LON_DIFF:
            continue

        found_neighborhoods = fetch_neighborhoods(current_bbox)

        # Only subdivide if the API returned *some* neighborhood info for this box
        if not found_neighborhoods:
            continue

        # Check for targets
        found_targets = found_neighborhoods.intersection(target_neighborhoods)
        if found_targets:
            print(f"!!! Found targets {found_targets} in {current_bbox}")
            # Store the specific targets found in this box
            if current_bbox not in candidate_boxes:
                candidate_boxes[current_bbox] = set()
            candidate_boxes[current_bbox].update(found_targets)
            all_found_targets.update(found_targets)

        # Subdivide
        mid_lat = (lat_min + lat_max) / 2
        mid_lon = (lon_min + lon_max) / 2

        quadrants = [
            f"{lat_min},{lon_min},{mid_lat},{mid_lon}",
            f"{lat_min},{mid_lon},{mid_lat},{lon_max}",
            f"{mid_lat},{lon_min},{lat_max},{mid_lon}",
            f"{mid_lat},{mid_lon},{lat_max},{lon_max}"
        ]
        for q_box in quadrants:
            if q_box not in checked_boxes:
                 boxes_to_check.append(q_box)

    print("\n----------------------------------------")
    print("Subdivision Search Complete.")
    print(f"Found {len(candidate_boxes)} candidate boxes potentially containing target neighborhoods.")
    print(f"Target neighborhoods covered across all candidates: {all_found_targets}")
    missing_overall = target_neighborhoods - all_found_targets
    if missing_overall:
        print(f"Warning: Could not find boxes covering: {missing_overall}")

    # Filter redundant boxes (prefer smaller ones that cover the same targets)
    print("Filtering redundant boxes...")
    final_boxes_dict = {} # Store as {bbox: targets}
    candidate_items = sorted(candidate_boxes.items()) # Sort for consistent processing

    for box1, targets1 in candidate_items:
        is_redundant = False
        # Check against boxes already added to final_boxes_dict
        boxes_to_remove_from_final = []
        for box2, targets2 in final_boxes_dict.items():
            if box1 == box2: continue
            # Case 1: box1 is contained within box2, and box1 covers a subset or equal set of targets
            if is_contained(box1, box2) and targets1.issubset(targets2):
                 is_redundant = True
                 # print(f"Skipping {box1} (contained in {box2}, covers subset/equal targets)")
                 break 
            # Case 2: box2 is contained within box1, and box2 covers a subset or equal set of targets
            if is_contained(box2, box1) and targets2.issubset(targets1):
                 # Mark box2 for removal from final list, add box1 later if not redundant itself
                 # print(f"Marking {box2} for removal (contained in {box1}, covers subset/equal targets)")
                 boxes_to_remove_from_final.append(box2)
        
        # Remove marked boxes from final dict
        for b_rem in boxes_to_remove_from_final:
            if b_rem in final_boxes_dict:
                del final_boxes_dict[b_rem]

        # Add box1 if it wasn't found to be redundant by a larger box already in the final list
        if not is_redundant:
             final_boxes_dict[box1] = targets1

    removed_count = len(candidate_boxes) - len(final_boxes_dict)
    print(f"Removed {removed_count} redundant boxes.")
    print("----------------------------------------")

    final_boxes = sorted(list(final_boxes_dict.keys()))
    if final_boxes:
        # Verify coverage with final boxes
        final_coverage = set()
        for box in final_boxes:
            final_coverage.update(candidate_boxes.get(box, set())) # Use original candidate_boxes for target info
        print(f"Final boxes cover targets: {final_coverage}")
        final_missing = target_neighborhoods - final_coverage
        if final_missing:
             print(f"Warning: Final set missing targets: {final_missing}")

        bbox_list_str = ";".join(final_boxes)
        print(f"\n--- Final Recommended BBOX_LIST ({len(final_boxes)} boxes) --- \n{bbox_list_str}\n---------------------------------")
    else:
        print("No bounding boxes found that contain the target neighborhoods after filtering.")
        if candidate_boxes:
            unfiltered_list = ";".join(sorted(candidate_boxes.keys()))
            print(f"Consider using the unfiltered list of candidates ({len(candidate_boxes)}):\n{unfiltered_list}")

    print("\nRemember to install requests: pip install requests") 