#!/usr/bin/env python3
import urllib.request
import json
import ssl
import os
import sys
import argparse
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

API_BASE = "https://insightsdata.api.sfwmd.gov/v1/insights-data/cont/data"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_stations_from_file(filepath):
    stations = []
    with open(filepath, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if "#" in line:
            parts = line.split("#")[1].split()
            if len(parts) >= 2:
                name = parts[0]
                api_id = parts[1]
                stations.append({"name": name, "apiId": api_id})
    return stations

STATIONS = load_stations_from_file(os.path.join(SCRIPT_DIR, "station_Flow_r1.bp"))

def fetch_api_data(api_id, start_utc, end_utc):
    start_str = start_utc.strftime("%Y%m%d")
    end_str = end_utc.strftime("%Y%m%d")
    url = f"{API_BASE}?timeseriesIds={api_id}&reportType=timeseries&format=plot&startDate={start_str}&endDate={end_str}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {api_id}: {e}")
        return None

def convert_cfs_to_cms(cfs):
    return cfs * 0.028316846592

def convert_feet_to_m(feet):
    return feet * 0.3048

def parse_timeseries_data(api_data):
    if not api_data or "timeseries" not in api_data or len(api_data["timeseries"]) == 0:
        return []
    ts = api_data["timeseries"][0]
    if not ts or "values" not in ts:
        return []
    return ts["values"]

def get_hour_key(dt):
    return dt.strftime("%Y-%m-%dT%H:00:00")

def generate_chart(station_name, values, temp_dir):
    timestamps = []
    flow_values = []
    for v in values:
        ts_val = v["x"]
        if isinstance(ts_val, int):
            dt = datetime.utcfromtimestamp(ts_val / 1000)
        else:
            ts = str(ts_val)
            dt = datetime.fromisoformat(ts.replace("Z", "").replace("+00:00", ""))
        timestamps.append(dt)
        
        y_val = v.get("y")
        if y_val is None:
            y_str = v.get("yStr")
            if y_str:
                try:
                    cfs = max(0, float(y_str))
                except:
                    cfs = 0
            else:
                cfs = 0
        else:
            cfs = max(0, float(y_val))
        flow_values.append(convert_cfs_to_cms(cfs))
    
    if not timestamps:
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, flow_values, linewidth=0.8)
    plt.xlabel('Time')
    plt.ylabel('Flow (CMS)')
    plt.title(f'{station_name} - Flow Data')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(temp_dir, f"{station_name}.png"), dpi=100)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Fetch flow data from SFWMD DBHYDRO API")
    parser.add_argument("--days", type=int, default=61, help="Number of days to look back (default: 61)")
    parser.add_argument("--png", action="store_true", help="Generate PNG charts")
    args = parser.parse_args()

    EDT_OFFSET = 4

    now = datetime.now()
    end_edt = now.replace(hour=23, minute=0, second=0, microsecond=0)
    start_edt = (now - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)

    start_utc = start_edt - timedelta(hours=EDT_OFFSET)
    end_utc = end_edt - timedelta(hours=EDT_OFFSET)

    print(f"EDT range: {start_edt.strftime('%Y-%m-%d %H:%M')} to {end_edt.strftime('%Y-%m-%d %H:%M')}")
    print(f"UTC range: {start_utc.strftime('%Y-%m-%d %H:%M')} to {end_utc.strftime('%Y-%m-%d %H:%M')}")

    hour_buckets = {}
    current = start_utc
    while current <= end_utc:
        key = get_hour_key(current)
        hour_buckets[key] = {"data": {s["name"]: [] for s in STATIONS}}
        current += timedelta(hours=1)

    all_data = {}
    temp_dir = os.path.join(SCRIPT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    for station in STATIONS:
        print(f"Fetching {station['name']} ({station['apiId']})...")
        api_data = fetch_api_data(station["apiId"], start_utc, end_utc)
        if api_data:
            values = parse_timeseries_data(api_data)
            all_data[station["name"]] = values
            if args.png:
                generate_chart(station["name"], values, temp_dir)
            print(f" Got {len(values)} values")
        else:
            all_data[station["name"]] = []

    for station_name, values in all_data.items():
        for v in values:
            ts_val = v["x"]
            if isinstance(ts_val, int):
                dt = datetime.utcfromtimestamp(ts_val / 1000)
            else:
                ts = str(ts_val)
                dt = datetime.fromisoformat(ts.replace("Z", "").replace("+00:00", ""))
            dt = dt.replace(minute=0, second=0, microsecond=0)

            if dt < start_utc or dt > end_utc:
                continue

            y_val = v.get("y")
            if y_val is None:
                y_str = v.get("yStr")
                if y_str:
                    try:
                        cfs = max(0, float(y_str))
                    except:
                        cfs = 0
                else:
                    cfs = 0
            else:
                cfs = max(0, float(y_val))
            cms = convert_cfs_to_cms(cfs)

            key = get_hour_key(dt)
            if key in hour_buckets:
                hour_buckets[key]["data"][station_name].append(cms)

    output_lines = []
    for hour_key in sorted(hour_buckets.keys()):
        dt = datetime.fromisoformat(hour_key)
        hour_num = dt.hour
        if dt.date() == start_utc.date() and hour_num < start_utc.hour:
            continue
        if dt.date() == end_utc.date() and hour_num > end_utc.hour:
            continue

        dt_edt = dt + timedelta(hours=EDT_OFFSET)
        total_seconds = int((dt_edt - start_edt).total_seconds())

        line = f"{total_seconds:08d}"

        for station in STATIONS:
            vals = hour_buckets[hour_key]["data"].get(station["name"], [])
            if vals:
                avg_val = sum(vals) / len(vals)
            else:
                avg_val = 0.0
            if avg_val == 0:
                line += " 0.00"
            else:
                line += f" {avg_val:.2f}"

        output_lines.append(line)

    for i in range(7 * 24):
        total_seconds += 3600
        line = f"{total_seconds:08d}" + " 0.00" * len(STATIONS)
        output_lines.append(line)

    with open(os.path.join(SCRIPT_DIR, "flow_output.txt"), "w") as f:
        f.write("\n".join(output_lines))

    print(f"Output written to flow_output.txt ({len(output_lines)} lines)")

if __name__ == "__main__":
    main()