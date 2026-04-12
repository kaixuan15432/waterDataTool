# SECOORA Station Data Scraper

A Python script that fetches water temperature and salinity data from SECOORA (Southeast Coastal Ocean Observing Regional Association) stations based on specified date and time.

## Overview

This script reads station URLs from `station.txt`, queries the SECOORA ERDDAP API to retrieve station metadata (name, latitude, longitude) and observation data (water temperature and salinity) for a specified date/time, and outputs the results to two files:

- `secoora_output.txt` - CSV format (comma-separated)
- `secoora_output_format.txt` - Formatted table with aligned columns

## Requirements

- Python 3.x
- Internet connection (to access SECOORA ERDDAP API)

No external packages required - uses only standard library modules.

## File Structure

```
dataTool/
├── station.txt                  # Input: Station URLs and names
├── secoora_scraper.py           # Main script
├── secoora_output.txt           # Output: CSV format
├── secoora_output_format.txt    # Output: Formatted table
├── update_station.py            # Utility: Fetch station names from API
└── README.md                    # This file
```

## Usage

### Basic Usage

```bash
python secoora_scraper.py
```

Uses default date (2026-03-01) and time (05:00:00).

### Specify Date and Time

```bash
python secoora_scraper.py 2026-03-15 10:00:00
```

Arguments:
- Argument 1: Date in YYYY-MM-DD format
- Argument 2: Time in HH:MM:SS format (optional)

### Output Files

**secoora_output.txt** (CSV format):
```
01,26.4595,-81.9518,22.0,34.69,Gulf Star Marina
02,26.453428,-82.035537,20.71,35.42,Sanibel Dock
...
```

**secoora_output_format.txt** (Aligned format):
```
01    26.459500  -81.951800    22.00    34.69  Gulf Star Marina
02    26.453428  -82.035537    20.71    35.42  Sanibel Dock
...
```

## Adding New Stations

### Station File Format

Edit `station.txt` with one station per line. Each line has two parts separated by comma:

```
SECOORA_PORTAL_URL,Station_Name
```

### Format Rules

1. **URL format**: `https://portal.secoora.org/#metadata/{ID}/station`
   - Replace `{ID}` with the actual metadata ID number

2. **Station name**: Optional, can be left empty
   - If empty, the script will fetch the name from the API
   - If provided, the saved name takes priority over API name

### Example Entries

```
# Single station with name
https://portal.secoora.org/#metadata/130077/station,Gulf Star Marina

# Station without name (will be fetched from API)
https://portal.secoora.org/#metadata/134984/station,

# Comment lines (start with #)
# https://portal.secoora.org/#metadata/123456/station,New Station
```

### How to Find Station URLs

1. Visit [SECOORA Data Portal](https://portal.secoora.org/)
2. Browse or search for stations
3. Copy the station metadata URL
4. Add to `station.txt` in the format shown above

### Updating Station Names

If you want to fetch station names from the API and update `station.txt`:

```bash
python update_station.py
```

This will query the ERDDAP API for each station ID and update the station names in `station.txt`.

## Data Source

- **API**: SECOORA ERDDAP (https://erddap.secoora.org)
- **Variables retrieved**:
  - `sea_water_temperature` - Water temperature in degree Celsius
  - `sea_water_practical_salinity` - Salinity in PSS (Practical Salinity Scale)

## Error Handling

- If a station is not found in ERDDAP: skipped with "No dataset found" message
- If no data available for the specified time: skipped with "No data" message
- Network errors: logged but script continues processing other stations

## Notes

- The script processes all stations in `station.txt` that have valid metadata IDs
- Data availability depends on the specific station's historical records
- Some stations may have no data for the requested date/time
- Latitude/Longitude coordinates are in decimal degrees (WGS84)