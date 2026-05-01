# get_flow_data.py

Fetch flow data from SFWMD API and output to flow_output.txt.

## Usage

```bash
python3 get_flow_data.py
python3 get_flow_data.py --png # Also generate PNG charts
```

## Output

- `flow_output.txt` - Flow data text file (hourly averaged, EDT timezone)
- `temp/` - PNG charts folder (only generated when using --png flag)

## Data Source

API: `https://insightsdata.api.sfwmd.gov/v1/insights-data/cont/data`

Station configuration is read from `station_Flow_r1.bp`, containing 23 flow stations.

## Time Range

- Fetches data for the 61 days prior to current time
- API queries use `startDate/endDate` parameters for historical data access
- EDT timezone (UTC-4): API returns UTC timestamps, converted to EDT for output
  - EDT 00:00 = UTC 20:00 (previous day), so API query starts 1 day earlier to cover EDT midnight

## Data Processing

- Raw data is at 5-minute intervals from the API
- All data points within the same hour are averaged to produce hourly values
- This avoids issues where exact top-of-hour readings may be 0 while intra-hour data exists
- Output format: `total_seconds station1_val station2_val ...` (seconds from EDT start)