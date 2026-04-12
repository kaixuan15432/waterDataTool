#!/usr/bin/env python3
import urllib.request
import json
import re

def search_erddap_dataset(metadata_id):
    url = f"https://erddap.secoora.org/erddap/search/index.json?page=1&itemsPerPage=10&searchFor={metadata_id}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            rows = data.get('table', {}).get('rows', [])
            if rows:
                return rows[0][6]
    except Exception as e:
        print(f"  Error: {e}")
    return None

with open('station.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Processing {len(lines)} stations...")

results = []

for url in lines:
    match = re.search(r'metadata/(\d+)', url)
    if match:
        sid = match.group(1)
        name = search_erddap_dataset(sid)
        if name:
            print(f"{sid}: {name}")
            results.append((url, name))
        else:
            print(f"{sid}: Not found")
            results.append((url, ""))

with open('station.txt', 'w') as f:
    for url, name in results:
        f.write(f"{url},{name}\n")

print(f"\nUpdated station.txt with {len(results)} station names")