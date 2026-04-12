#!/usr/bin/env python3
import urllib.request
import json
import re
import sys

TARGET_DATE = "2026-03-01"
TARGET_TIME = "05:00:00"

if len(sys.argv) >= 3:
    TARGET_DATE = sys.argv[1]
    TARGET_TIME = sys.argv[2]
    print(f"Using input date: {TARGET_DATE}, time: {TARGET_TIME}")
elif len(sys.argv) >= 2:
    TARGET_DATE = sys.argv[1]
    print(f"Using input date: {TARGET_DATE}")
else:
    print("Usage: python secoora_scraper.py [date] [time]")
    print(f"Default: {TARGET_DATE} {TARGET_TIME}")

def search_erddap_dataset(metadata_id):
    url = f"https://erddap.secoora.org/erddap/search/index.json?page=1&itemsPerPage=10&searchFor={metadata_id}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            rows = data.get('table', {}).get('rows', [])
            if rows:
                return rows[0][15], rows[0][6]
    except Exception as e:
        print(f"  Search error: {e}")
    return None, None

def get_station_location(dataset_id):
    url = f"https://erddap.secoora.org/erddap/info/{dataset_id}/index.json"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            lat, lon = None, None
            for row in data.get('table', {}).get('rows', []):
                if row[0] == 'attribute' and row[1] == 'NC_GLOBAL':
                    if row[2] == 'station':
                        for r2 in data['table']['rows']:
                            if r2[0] == 'variable' and r2[1] == 'station':
                                for r3 in data['table']['rows']:
                                    if r3[0] == 'attribute' and r3[1] == 'station' and r3[2] == 'ioos_code':
                                        match = re.search(r':([-\d.]+),([-\d.]+)$', str(r3[3]))
                                        if match:
                                            lat, lon = float(match.group(1)), float(match.group(2))
            return lat, lon
    except Exception as e:
        print(f"  Location error: {e}")
    return None, None

def get_station_data(dataset_id, target_date, target_time):
    url = f"https://erddap.secoora.org/erddap/tabledap/{dataset_id}.csv?station,latitude,longitude,time,sea_water_practical_salinity,sea_water_temperature&time={target_date}T{target_time}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode()
            lines = content.strip().split('\n')
            if len(lines) >= 3:
                last_line = lines[-1]
                parts = last_line.split(',')
                if len(parts) >= 6:
                    lat = parts[1]
                    lon = parts[2]
                    sal = parts[4]
                    temp = parts[5]
                    return lat, lon, sal, temp
    except Exception as e:
        print(f"  Data error: {e}")
    return None, None, None, None

with open('station.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

station_data = []
for line in lines:
    url = line.split(',')[0]
    name = line.split(',', 1)[1] if ',' in line else ''
    match = re.search(r'metadata/(\d+)', url)
    if match:
        station_data.append({'url': url, 'name': name, 'sid': match.group(1)})

print(f"Found {len(station_data)} station IDs")

results = []

for sd in station_data:
    sid = sd['sid']
    saved_name = sd['name']
    url = sd['url']
    print(f"\nProcessing: {sid}")
    
    dataset_id, api_name = search_erddap_dataset(sid)
    if not dataset_id:
        print(f"  No dataset found")
        continue
    
    name = saved_name if saved_name else api_name
    print(f"  Dataset: {dataset_id}, Name: {name}")
    
    lat, lon, sal, temp = get_station_data(dataset_id, TARGET_DATE, TARGET_TIME)
    
    if not lat or not lon:
        lat = "NaN"
        lon = "NaN"
    if not sal or sal == 'NaN':
        sal = "NaN"
    if not temp or temp == 'NaN':
        temp = "NaN"
    
    print(f"  Location: {lat}, {lon}, Data: Temp={temp}°C, Salinity={sal}")
    results.append({
        'url': url,
        'name': name,
        'lat': lat,
        'lon': lon,
        'temp': temp,
        'sal': sal
    })

print(f"\n{'='*60}")
print(f"Results: {len(results)}")

with open('secoora_output.txt', 'w') as f:
    for i, r in enumerate(results, 1):
        idx = f"{i:02d}"
        line = f"{idx},{r['lat']},{r['lon']},{r['temp']},{r['sal']},{r['name']}"
        f.write(line + "\n")
        print(line)

with open('secoora_output_format.txt', 'w') as f:
    for i, r in enumerate(results, 1):
        idx = f"{i:02d}"
        lat = f"{float(r['lat']):>10.6f}"
        lon = f"{float(r['lon']):>11.6f}"
        temp = f"{float(r['temp']):>8.2f}"
        sal = f"{float(r['sal']):>8.2f}"
        line = f"{idx:<4} {lat} {lon} {temp} {sal}  {r['name']}"
        f.write(line + "\n")

print(f"\nSaved to: secoora_output.txt and secoora_output_format.txt")