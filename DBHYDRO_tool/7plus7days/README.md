# get_flow_data.py

Fetch flow data from SFWMD API and output to flow_output.txt.

## Usage

```bash
python3 get_flow_data.py
python3 get_flow_data.py --png  # Also generate PNG charts
```

## Output

- `flow_output.txt` - Flow data text file
- `temp/` - PNG charts folder (only generated when using --png flag)

## Data Source

Station configuration is read from `station_Flow_r1.bp`, containing 23 flow stations.

## Time Range

Automatically fetches data for the 7 days prior to current time.