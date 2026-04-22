# get_salinity_temperature.py

Fetch salinity and temperature data from SFWMD DBHYDRO API for specified time.

## Usage

```bash
python3 get_salinity_temperature.py --time "M/D/YYYY H:MMam/pm"
python3 get_salinity_temperature.py --time "1/1/2026 5:00am" --start 20260101 --end 20260110
```

## Parameters

- `--time` (required): Target time in format `M/D/YYYY H:MMam/pm` (e.g., `1/1/2026 5:00am`)
- `--start` (optional): Start date YYYYMMDD for API query range (default: target time ± 1 day)
- `--end` (optional): End date YYYYMMDD for API query range (default: target time ± 1 day)

## Output

- `output.txt` - Station data with format: `seq lon lat salinity temperature`

## Station Files

- `DBHYDRO_salinity-1.bp` - Salinity station configuration (100 stations)
- `DBHYDRO_temp.bp` - Temperature station configuration (46 stations)

## Data Source

API: `https://insightsdata.api.sfwmd.gov/v1/insights-data/cont/data`

Time zone: EDT (UTC-4), converted automatically to UTC for API query.