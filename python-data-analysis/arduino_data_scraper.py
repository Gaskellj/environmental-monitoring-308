from datetime import datetime, timezone, timedelta
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from iot_api_client import ApiClient, Configuration
from iot_api_client.api.properties_v2_api import PropertiesV2Api
import pandas as pd
import os

# Change these to your own values
API_CLIENT_ID     = "HbFHAQZDuYdVbrOoYwDHUG8Nl18nOQRF"
API_CLIENT_SECRET = "ZZIFNkc3CPRJ6LKvnJPZDKtIOIMzAyF6rWTaDJcRCazIAevkRMdy5jMGjr5sHIt0"
THING_ID          = "2964b461-851a-45fd-a2e4-93aea1ce8d0f"
TOKEN_URL         = "https://api2.arduino.cc/iot/v1/clients/token"

# where we store the cumulative data
data_dir  = os.path.join(os.path.dirname(__file__), "data")
data_file = os.path.join(data_dir, "arduino_data.csv")

# API will return at most this many points per call
MAX_RECORDS = 1000

def parse_time(ts) -> datetime:
    """Convert Arduino ISO timestamp (or datetime) to a datetime object."""
    # If it's already a datetime, return as-is
    if isinstance(ts, datetime):
        return ts
    # ts is a string
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
    target     = {"pH", "temperature", "turbidity", "dissolved_oxygen"}
    selected   = [p for p in properties if p["name"] in target]

    # 3. DETERMINE TIME WINDOW
    now = datetime.now(timezone.utc)
    if os.path.exists(data_file):
        df_old = pd.read_csv(data_file, index_col="datetime", parse_dates=True)
        # localize old index to UTC for consistency
        if df_old.index.tz is None:
            df_old.index = df_old.index.tz_localize(timezone.utc)
        past   = df_old.index.max()
    else:
        df_old = None
        past    = now - timedelta(days=7)
    past_iso = past.isoformat()

    # 4. SETUP API CLIENT
    cfg             = Configuration(host="https://api2.arduino.cc")
    cfg.access_token = token["access_token"]
    api_client      = ApiClient(cfg)
    prop_api        = PropertiesV2Api(api_client)

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

        times  = [parse_time(dp.time) for dp in all_points]
        values = [dp.value for dp in all_points]
        series_dict[prop["name"]] = pd.Series(data=values, index=times, name=prop["name"])

    df_new = pd.DataFrame(series_dict)
    df_new.index.name = "timestamp"

    # Drop rows where all sensors are zero
    if not df_new.empty:
        df_new = df_new.loc[(df_new != 0).any(axis=1)]

    # Merge with old data
    if df_old is not None:
        df = pd.concat([df_old, df_new])
        df = df[~df.index.duplicated(keep="first")]
    else:
        df = df_new

    df.sort_index(inplace=True)

    # Round values and forward-fill
    df = df.round(1).ffill()

    # Drop timezone from index
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # Prepare final DataFrame with desired columns and names
    df_final = df.reset_index().rename(
        columns={
            'timestamp': 'datetime',
            'turbidity': 'turbidity_value',
            'temperature': 'temp_value',
            'pH': 'pH_value'
        }
    )

    # Keep only the specified columns
    df_final = df_final[['datetime', 'turbidity_value', 'temp_value', 'pH_value']]
    return df_final


def save_data(df: pd.DataFrame):
    os.makedirs(data_dir, exist_ok=True)
    df.to_csv(data_file, index=False)


if __name__ == "__main__":
    df = get_arduino_data()
    print(f"Retrieved {len(df)} rows of data")
    save_data(df)
