#!/usr/bin/env python3
import urllib.request
import json
import ssl
import os
from datetime import datetime, timedelta

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

def fetch_api_data(api_id, target_dt):
    url = f"{API_BASE}?timeseriesIds={api_id}&reportType=timeseries&format=plot&period=1week"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            api_data = json.loads(response.read().decode())
        
        if api_data and "timeseries" in api_data and len(api_data["timeseries"]) > 0:
            ts = api_data["timeseries"][0]
            if ts and "values" in ts:
                values = ts["values"]
                for v in values:
                    ts_val = v["x"]
                    if isinstance(ts_val, int):
                        dt = datetime.utcfromtimestamp(ts_val / 1000)
                    else:
                        dt = datetime.fromisoformat(str(ts_val).replace("Z", "").replace("+00:00", ""))
                    
                    if dt.year == target_dt.year and dt.month == target_dt.month and dt.day == target_dt.day and dt.hour == target_dt.hour:
                        y_val = v.get("y")
                        if y_val is None:
                            y_str = v.get("yStr")
                            if y_str:
                                return y_str
                        else:
                            return y_val
    except Exception as e:
        print(f"Error fetching {api_id}: {e}")
    return None

def main():
    now = datetime.now()
    target_date = now - timedelta(days=7)
    target_hour_edt = 5
    target_hour_utc = target_hour_edt + 4
    
    target_dt = target_date.replace(hour=target_hour_utc, minute=0, second=0, microsecond=0)
    
    print(f"Target date: {target_date.strftime('%Y-%m-%d')} EDT {target_hour_edt}:00")
    print(f"Target UTC: {target_dt.strftime('%Y-%m-%d %H:%M')}")
    
    bp_file = os.path.join(SCRIPT_DIR, "DBHYDRO_salinity.bp")
    stations = load_stations_from_file(bp_file)
    
    print(f"Loaded {len(stations)} stations")
    
    results = []
    for station in stations:
        api_id = station["api_id"]
        if api_id:
            fetched_val = fetch_api_data(api_id, target_dt)
            if fetched_val is not None:
                station["data"] = fetched_val
            else:
                print(f"No data for {station['name']} ({api_id})")
        
        results.append((station["seq"], station["lon"], station["lat"], station["data"]))
    
    output_file = os.path.join(SCRIPT_DIR, "output_salinity.txt")
    with open(output_file, "w") as f:
        for seq, lon, lat, val in results:
            f.write(f"{seq} {lon} {lat} {val}\n")
    
    print(f"Output written to {output_file}")

if __name__ == "__main__":
    main()
