#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from iot_api_client import ApiClient, Configuration
from iot_api_client.api.properties_v2_api import PropertiesV2Api
import pandas as pd
import os

API_CLIENT_ID     = "HbFHAQZDuYdVbrOoYwDHUG8Nl18nOQRF"
API_CLIENT_SECRET = "ZZIFNkc3CPRJ6LKvnJPZDKtIOIMzAyF6rWTaDJcRCazIAevkRMdy5jMGjr5sHIt0"
THING_ID          = "2964b461-851a-45fd-a2e4-93aea1ce8d0f"
TOKEN_URL         = "https://api2.arduino.cc/iot/v1/clients/token"

# where we store the cumulative data
DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "arduino_data.csv")

# API will return at most this many points per call
MAX_RECORDS = 1000

def parse_time(ts: str) -> datetime:
    """Convert Arduino ISO timestamp (possibly ending with Z) to a datetime object."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)

def get_arduino_data() -> pd.DataFrame:
    # 1. AUTH
    client = BackendApplicationClient(client_id=API_CLIENT_ID)
    oauth  = OAuth2Session(client=client)
    token  = oauth.fetch_token(
        token_url=TOKEN_URL,
        client_id=API_CLIENT_ID,
        client_secret=API_CLIENT_SECRET,
        include_client_id=True,
        audience="https://api2.arduino.cc/iot"
    )

    # 2. METADATA
    props_resp = oauth.get(f"https://api2.arduino.cc/iot/v1/things/{THING_ID}/properties")
    props_resp.raise_for_status()
    properties = props_resp.json()
    target     = {"pH", "temperature", "turbidity", "tds"}
    selected   = [p for p in properties if p["name"] in target]

    # 3. DETERMINE TIME WINDOW
    now = datetime.now(timezone.utc)
    if os.path.exists(DATA_FILE):
        df_old = pd.read_csv(DATA_FILE, index_col="timestamp", parse_dates=True)
        past   = df_old.index.max()
    else:
        df_old = None
        past    = now - timedelta(days=7)
    past_iso = past.isoformat()

    # 4. SETUP API CLIENT
    cfg         = Configuration(host="https://api2.arduino.cc")
    cfg.access_token = token["access_token"]
    api_client  = ApiClient(cfg)
    prop_api    = PropertiesV2Api(api_client)

    # 5. FETCH & PAGE for each property
    series_dict = {}
    for prop in selected:
        all_points = []
        to_time    = now

        while True:
            resp = prop_api.properties_v2_timeseries(
                id=THING_ID,
                pid=prop["id"],
                interval=1,
                var_from=past_iso,
                to=to_time.isoformat(),
                desc=True
            )
            data = resp.data
            if not data:
                break
            all_points.extend(data)
            if len(data) < MAX_RECORDS:
                break
            oldest_ts = data[-1].time
            oldest_dt = parse_time(oldest_ts)
            to_time    = oldest_dt - timedelta(microseconds=1)

        times  = [dp.time for dp in all_points]
        values = [dp.value for dp in all_points]
        series_dict[prop["name"]] = pd.Series(data=values, index=times, name=prop["name"])

    df_new = pd.DataFrame(series_dict)
    df_new.index.name = "timestamp"

    # DROP records where all sensors are zero
    if not df_new.empty:
        df_new = df_new.loc[(df_new != 0).any(axis=1)]

    # 6. MERGE WITH OLD (if present), remove dupes, sort
    if df_old is not None:
        df = pd.concat([df_old, df_new])
        df = df[~df.index.duplicated(keep="first")]
    else:
        df = df_new

    df.sort_index(inplace=True)
    return df

def save_data(df: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(DATA_FILE, index=True)
    print(f"Saved data to {DATA_FILE}")

if __name__ == "__main__":
    df = get_arduino_data()
    print(f"Retrieved {len(df)} rows of data")
    save_data(df)
