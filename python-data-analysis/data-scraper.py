import requests
import time
from datetime import datetime

# Replace with your actual API key and Thing ID
API_KEY = "HbFHAQZDuYdVbrOoYwDHUG8Nl18nOQRF"
THING_ID = "44f23f80-3e5e-43a7-b951-9fc88ba0c229"

# Map sensor names to their variable IDs
VARIABLE_IDS = ['pH', 'tds', 'temperature', 'turbidity']

# Set the start and end time for the data retrieval (Unix timestamps)
end_time = int(time.time())
start_time = end_time - 3600  # last hour

def get_historical_data(variable_id, start_ts, end_ts):
    url = (f"https://api2.arduino.cc/iot/v2/things/{THING_ID}/variables/{variable_id}/history?from={start_ts}&to={end_ts}")
    headers = { "Authorization": f"Bearer {API_KEY}" }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("entries", [])
    else:
        print(f"Error fetching {variable_id}: {resp.status_code} – {resp.text}")
        return []

for variable in VARIABLE_IDS:
    entries = get_historical_data(variable, start_time, end_time)
    print(f"\n=== {variable} Data (last hour) ===")
    if not entries:
        print("  No data found.")
        continue
    for entry in entries:
        # entry["ts"] is an ISO8601 timestamp; convert to human‐readable if you like:
        ts = entry.get("ts")
        try:
            human_ts = datetime.fromisoformat(ts.rstrip("Z")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            human_ts = ts
        value = entry.get("value")
        print(f"  {human_ts} → {value}")
