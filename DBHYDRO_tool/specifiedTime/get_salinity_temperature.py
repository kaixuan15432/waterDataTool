#!/usr/bin/env python3
import urllib.request
import json
import ssl
import os
import sys
from datetime import datetime, timedelta
import argparse

API_BASE = "https://insightsdata.api.sfwmd.gov/v1/insights-data/cont/data"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_stations_from_file(filepath):
    stations = []
    with open(filepath, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("all "):
            continue
        parts = line.split("#")[0].split()
        if len(parts) >= 4:
            seq = parts[0]
            lon = parts[1]
            lat = parts[2]
            data_val = parts[3]
            name = ""
            api_id = ""
            if "#" in line:
                comment = line.split("#")[1].strip()
                comment_parts = comment.split()
                if len(comment_parts) >= 2:
                    name = comment_parts[0]
                    api_id = comment_parts[1]
            stations.append({"seq": seq, "lon": lon, "lat": lat, "data": data_val, "name": name, "api_id": api_id})
    return stations

def fetch_api_data(api_id, target_dt, start_date_str="20260101", end_date_str="20260110"):
    url = f"{API_BASE}?timeseriesIds={api_id}&reportType=timeseries&format=plot&startDate={start_date_str}&endDate={end_date_str}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    target_date_edt = target_dt - timedelta(hours=4)

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            api_data = json.loads(response.read().decode())

        if api_data and "timeseries" in api_data and len(api_data["timeseries"]) > 0:
            ts = api_data["timeseries"][0]
            if ts and "values" in ts:
                values = ts["values"]
                hourly_val = None
                daily_val = None
                for v in values:
                    ts_val = v["x"]
                    if isinstance(ts_val, int):
                        dt = datetime.utcfromtimestamp(ts_val / 1000)
                    else:
                        dt = datetime.fromisoformat(str(ts_val).replace("Z", "").replace("+00:00", ""))

                    freq = v.get("frequency", "")
                    y_val = v.get("y")
                    if y_val is None:
                        y_str = v.get("yStr")
                        y_val = y_str if y_str else None

                    if freq == "DA":
                        if daily_val is None and dt.year == target_date_edt.year and dt.month == target_date_edt.month and dt.day == target_date_edt.day:
                            daily_val = y_val
                    else:
                        if hourly_val is None and dt.year == target_dt.year and dt.month == target_dt.month and dt.day == target_dt.day and dt.hour == target_dt.hour:
                            hourly_val = y_val

                if hourly_val is not None:
                    return hourly_val
                if daily_val is not None:
                    return daily_val
    except Exception as e:
        print(f"Error fetching {api_id}: {e}")
        return None

def parse_time_input(time_str):
    time_str = time_str.strip()
    for fmt in ["%m/%d/%Y %I:%M%p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"]:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt
        except ValueError:
            continue
    raise ValueError(f"Invalid time format: {time_str}. Use format like: 1/1/2026 5:00am")

def main():
    parser = argparse.ArgumentParser(description="Fetch salinity and temperature data from DBHYDRO")
    parser.add_argument("--time", default="1/1/2026 5:00am", help="Target time (format: M/D/YYYY H:MMam/pm)")
    parser.add_argument("--start", default="", help="Start date YYYYMMDD (optional)")
    parser.add_argument("--end", default="", help="End date YYYYMMDD (optional)")
    args = parser.parse_args()
    
    target_dt = parse_time_input(args.time)
    target_hour_utc = target_dt.hour + 4

    if target_hour_utc >= 24:
        target_hour_utc -= 24
        target_dt = target_dt + timedelta(days=1)

    target_dt = target_dt.replace(hour=target_hour_utc, minute=0, second=0, microsecond=0)
    
    if args.start and args.end:
        start_str = args.start
        end_str = args.end
    else:
        start_date = target_dt - timedelta(days=1)
        end_date = target_dt + timedelta(days=1)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
    
    print(f"Target time: {args.time}")
    print(f"Target UTC: {target_dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"Date range: {start_str} to {end_str}")
    
    bp_file = os.path.join(SCRIPT_DIR, "DBHYDRO_salinity-1.bp")
    stations = load_stations_from_file(bp_file)

    temp_file = os.path.join(SCRIPT_DIR, "DBHYDRO_temp.bp")
    temp_stations = load_stations_from_file(temp_file)

    print(f"Loaded {len(stations)} salinity stations")
    print(f"Loaded {len(temp_stations)} temperature stations")

    salinity_results = []
    for station in stations:
        salinity_api_id = station["api_id"]
        if salinity_api_id:
            fetched_val = fetch_api_data(salinity_api_id, target_dt, start_str, end_str)
            if fetched_val is not None:
                salinity_results.append((args.time, station["name"], station["lon"], station["lat"], fetched_val))
            else:
                print(f"No salinity data for {station['name']} ({salinity_api_id})")

    temp_results = []
    for station in temp_stations:
        temp_api_id = station["api_id"]
        if temp_api_id:
            fetched_val = fetch_api_data(temp_api_id, target_dt, start_str, end_str)
            if fetched_val is not None:
                temp_results.append((args.time, station["name"], station["lon"], station["lat"], fetched_val))
            else:
                print(f"No temperature data for {station['name']} ({temp_api_id})")

    sal_file = os.path.join(SCRIPT_DIR, "output_salinity.txt")
    with open(sal_file, "w") as f:
        for time_str, name, lon, lat, sal in salinity_results:
            f.write(f"{time_str} {name} {lon} {lat} {sal}\n")
    print(f"Salinity output written to {sal_file} ({len(salinity_results)} stations)")

    temp_file_out = os.path.join(SCRIPT_DIR, "output_temperature.txt")
    with open(temp_file_out, "w") as f:
        for time_str, name, lon, lat, temp in temp_results:
            f.write(f"{time_str} {name} {lon} {lat} {temp}\n")
    print(f"Temperature output written to {temp_file_out} ({len(temp_results)} stations)")

if __name__ == "__main__":
    main()