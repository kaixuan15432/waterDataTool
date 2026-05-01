#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

def load_station_names(bp_path):
    names = []
    with open(bp_path, "r") as f:
        for line in f:
            line = line.strip()
            if "#" in line:
                parts = line.split("#")[1].split()
                if len(parts) >= 1:
                    names.append(parts[0])
    return names

def main():
    parser = argparse.ArgumentParser(description="Plot flow data charts")
    parser.add_argument("--days", type=int, default=61, help="Number of days to look back (default: 61)")
    args = parser.parse_args()

    bp_path = os.path.join(PARENT_DIR, "station_Flow_r1.bp")
    data_path = os.path.join(PARENT_DIR, "flow_output.txt")

    station_names = load_station_names(bp_path)
    if not station_names:
        print("No stations found in bp file")
        return

    now = datetime.now()
    start_edt = (now - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)

    timestamps = []
    station_data = [[] for _ in station_names]

    with open(data_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 1 + len(station_names):
                continue
            total_seconds = int(parts[0])
            dt = start_edt + timedelta(seconds=total_seconds)
            timestamps.append(dt)
            for i, name in enumerate(station_names):
                station_data[i].append(float(parts[i + 1]))

    print(f"Loaded {len(timestamps)} time points, {len(station_names)} stations")

    os.makedirs(SCRIPT_DIR, exist_ok=True)

    for i, name in enumerate(station_names):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(timestamps, station_data[i], linewidth=0.6, color='tab:blue')
        ax.set_xlabel('Time (EDT)')
        ax.set_ylabel('Flow (CMS)')
        ax.set_title(f'{name} - Flow Data ({args.days} days)')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        out_path = os.path.join(SCRIPT_DIR, f"{name}.png")
        plt.savefig(out_path, dpi=120)
        plt.close()
        print(f"Saved {out_path}")

    print(f"All {len(station_names)} charts saved to {SCRIPT_DIR}")

if __name__ == "__main__":
    main()