# Bounding Box Determination Plan

## 1. Objective

To identify the minimal set of bounding box coordinates (`bBox` values) necessary to consistently retrieve apartment listings from the target Yad2 neighborhoods (specifically IDs: **1461, 1520, 205**) via the `https://gw.yad2.co.il/realestate-feed/rent/map` API endpoint. The aim is to define these boxes _before_ implementing the multi-box fetching logic in the main script, allowing the final configuration to be more precise and avoid requiring manual `bBox` input during normal operation.

## 2. Methodology: Iterative API Testing (Trial & Error)

This phase involves manually querying the API with different bounding boxes and analyzing the results.

- **Tools:**
  - `curl` commands (similar to those executed previously in the development process).
  - Alternatively, a temporary, simple Python script using the `requests` library can be used for easier execution and potential result filtering.
- **Process:**
  1.  **Initial Request:** Start with a single, large bounding box known to cover the general Tel Aviv / Givatayim area (e.g., using coordinates from previous successful `curl` commands).
  2.  **Construct Query:** Formulate the full API URL. Include the test `bBox` value. Also include other parameters like `minPrice`, `maxPrice`, `minRooms`, `maxRooms` to ensure results are returned. Critically, include `multiNeighborhood=1461,1520,205` initially to help confirm the box _can_ contain the desired listings.
  3.  **Execute Request:** Run the `curl` command or script to fetch the JSON data.
  4.  **Analyze Response:** Carefully examine the `feedItems` array (or equivalent) in the returned JSON. For each listing, extract the `neighborhood_id` (or equivalent field name identified by inspecting the JSON structure).
  5.  **Evaluate Coverage & Precision:**
      - Are all target neighborhood IDs (1461, 1520, 205) represented in the results from this `bBox`?
      - Which other, undesired neighborhood IDs are also present?
      - Is the number of results reasonable, or is the box too large/small?
  6.  **Refine Bounding Box(es):**
      - **If targets missing:** Expand the current box or try adding additional, separate boxes targeting the missing areas.
      - **If too many undesired areas:** Narrow the current box, or split it into multiple smaller, more focused boxes.
      - Adjust the `zoom` parameter if using it during testing, although the final implementation will rely on `bBox` primarily.
  7.  **Iterate:** Repeat steps 2-6 with the refined bounding box(es).
  8.  **Document:** Keep a log of the `bBox` values tested and the key neighborhood IDs returned for each test run.

## 3. Outcome

The final output of this preparatory phase will be a single string ready for the `.env` file:

- **`BBOX_LIST` Value:** A string containing one or more bounding boxes, separated by semicolons (`;`). Each box formatted as `lat_min,lon_min,lat_max,lon_max`.
  - Example: `"32.05,34.73,32.07,34.76;32.07,34.78,32.09,34.81"`
- This string should represent the optimal set of coordinates found through the trial-and-error process.

## 4. Subsequent Implementation

Once the optimal `BBOX_LIST` string is determined and documented:

1.  The main script development will proceed.
2.  `src/config.py` will be updated to load the `BBOX_LIST` variable.
3.  `src/main.py` will be modified to parse `BBOX_LIST`, loop through each box, construct the URL, fetch data, and aggregate results before filtering/notifying.
4.  `.env.example` and `README.md` will be updated to document the `BBOX_LIST` variable.
5.  The `MULTI_NEIGHBORHOOD` variable might become unnecessary in the final `.env` configuration if the `BBOX_LIST` proves sufficiently precise.
