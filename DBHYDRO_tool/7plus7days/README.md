# 7plus7days - Flow Data Tool

Fetch flow data from SFWMD DBHYDRO API and generate hourly averaged output for South Florida water management stations.

## File Structure

```
7plus7days/
├── get_flow_data.py          # Main script: fetch API data → flow_output.txt
├── station_Flow_r1.bp        # Station configuration (23 stations)
├── flow_output.txt           # Generated output (hourly flow data)
├── README.md
├── temp/                     # Optional: charts from get_flow_data.py --png
│   └── <station>.png
└── image/
    ├── plot_flow.py          # Plotting script: flow_output.txt → per-station charts
    └── <station>.png         # Generated per-station flow charts
```

## Dependencies

- Python 3.6+
- `matplotlib` (for chart generation)

No additional `pip install` needed beyond `matplotlib` — all other imports are from the Python standard library (`urllib`, `json`, `ssl`, `argparse`, `datetime`).

## Workflow

**Step 1**: Fetch data and generate `flow_output.txt`

```bash
python3 get_flow_data.py                # Default: 61 days lookback
python3 get_flow_data.py --days 7       # Custom lookback period
python3 get_flow_data.py --start 2025-01-01 --end 2025-06-30  # Custom date range
python3 get_flow_data.py --start 2025-03-01 --png             # From date to today + PNG
python3 get_flow_data.py --days 30 --png # 30 days + inline PNG charts in temp/
```

**Step 2**: Generate per-station charts from the output file

```bash
python3 image/plot_flow.py              # Default: 61 days
python3 image/plot_flow.py --days 7     # Must match --days from step 1
python3 image/plot_flow.py --start 2025-01-01 --end 2025-06-30  # Must match step 1
```

## Scripts

### get_flow_data.py

Main script that fetches hourly-averaged flow data from the SFWMD API and writes it to `flow_output.txt`.

#### Parameters

- `--days N` — Number of days to look back from today (default: `61`)
- `--start YYYY-MM-DD` — Start date (inclusive)
- `--end YYYY-MM-DD` — End date (inclusive)
- `--png` — Also generate quick preview PNG charts in `temp/` folder

> **Note**: If both `--start` and `--end` are provided, `--days` is ignored. If only one of `--start`/`--end` is provided, the other defaults to today.

#### What it does

1. Reads station list from `station_Flow_r1.bp`
2. For each station, queries the API for the specified date range
3. Parses raw 5-minute interval data points
4. Averages all values within each hour to produce hourly flow values
5. Appends 7 days of zero-padding after the current time (forecast gap)
6. Writes output to `flow_output.txt`

### image/plot_flow.py

Reads `flow_output.txt` and generates a separate PNG chart for each station.

#### Parameters

- `--days N` — Number of days to look back (default: `61`)
- `--start YYYY-MM-DD` — Start date (must match `get_flow_data.py`)
- `--end YYYY-MM-DD` — End date (must match `get_flow_data.py`)

> **Note**: Parameters must match what was used in `get_flow_data.py` for the time axis to be correct.

## Parameters Reference

| Parameter | Script | Default | Description |
|-----------|--------|---------|-------------|
| `--days N` | both | `61` | Days to look back from today |
| `--start YYYY-MM-DD` | both | — | Start date (inclusive) |
| `--end YYYY-MM-DD` | both | — | End date (inclusive) |
| `--png` | `get_flow_data.py` | off | Generate inline PNG charts in `temp/` |

## Station Configuration (`station_Flow_r1.bp`)

Format: each line contains station metadata with the station name and API ID after the `#` marker.

```
<index> <longitude> <latitude> <default_value> #<station_name> <api_id>
```

Example:
```
1 -80.2866310 25.7386370 0.0 #G93 64745
```

### Station List (23 stations)

| # | Station Name | API ID | Location |
|---|-------------|--------|----------|
| 1 | G93 | 64745 | Miami Canal |
| 2 | S25_C | 65066 | C-6 / S-25 |
| 3 | S25A_C | 65059 | C-6 / S-25A |
| 4 | S27_S | 65069 | S-27 |
| 5 | S28_S | 65070 | S-28 |
| 6 | S22_S | 65054 | S-22 |
| 7 | S25B_S | 65065 | S-25B |
| 8 | S26_S | 65068 | S-26 |
| 9 | S123_S | 64824 | S-123 |
| 10 | S21_S | 65052 | S-21 |
| 11 | S21A_S | 65050 | S-21A |
| 12 | S20G_S | 65047 | S-20G |
| 13 | S20F_S | 65046 | S-20F |
| 14 | S20_S | 65048 | S-20 |
| 15 | S197_C | 64893 | C-11 / S-197 |
| 16 | S18_C | 64878 | C-6 / S-18 |
| 17 | S177_S | 64874 | S-177 |
| 18 | S199_P | 65041 | S-199 |
| 19 | G737_C | AN673 | C-11 / G737 |
| 20 | S200_P | 65042 | S-200 |
| 21 | S328_C | AN557 | C-11 / S-328 |
| 22 | S332DX1_C | 65083 | S-332DX1 |
| 23 | S176_S | 64873 | S-176 |

## Output Format (`flow_output.txt`)

```
TTTTTTTT V1 V2 V3 ... V23
```

- **TTTTTTTT** — 8-digit zero-padded total seconds from EDT start time (0 = first hour of `start_edt`)
- **V1..V23** — Flow values in CMS (m³/s), space-separated, 2 decimal places; `0.00` when no data available

Example:
```
00000000 0.00 0.00 0.00 0.00 0.00 0.00 0.00 12.26 0.00 0.00 5.36 0.00 0.21 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00
00003600 0.00 0.00 0.00 0.00 0.00 0.00 0.00 5.81 0.00 0.00 0.79 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00
```

- Each row is one hour (3600 seconds apart)
- Total lines = `days * 24 + 7 * 24` (historical data + 7 days zero-padded forecast)

## Data Source

API: `https://insightsdata.api.sfwmd.gov/v1/insights-data/cont/data`

Query format:
```
?timeseriesIds={api_id}&reportType=timeseries&format=plot&startDate={YYYYMMDD}&endDate={YYYYMMDD}
```

> **Note**: SSL certificate verification is disabled for this API connection.

## Time Range

- **Three modes** for specifying time range:
  1. `--start` + `--end`: Exact date range (both inclusive)
  2. `--start` only: From start date to today
  3. `--days N` (or no flag): N days back from today (default: 61)
- API queries use `startDate/endDate` parameters for historical data access
- **EDT timezone (UTC-4)**: API returns UTC timestamps, converted to EDT for output
- EDT 00:00 = UTC 20:00 (previous day), so API query starts 1 day earlier to cover EDT midnight
- After current time, **7 days of zero-padding** is appended for forecast gap (168 rows of `0.00`)

## Data Processing

- Raw data is at **5-minute intervals** from the API
- All data points within the same hour are averaged to produce hourly values
- This avoids issues where exact top-of-hour readings may be 0 while intra-hour data exists

## Unit Conversions

| From | To | Factor |
|------|----|--------|
| CFS (ft³/s) | CMS (m³/s) | × 0.028316846592 |

All output values are in CMS. The API returns CFS (cubic feet per second).