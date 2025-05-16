from datetime import datetime, timezone, timedelta
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from iot_api_client import ApiClient, Configuration
from iot_api_client.api.properties_v2_api import PropertiesV2Api

API_CLIENT_ID     = "HbFHAQZDuYdVbrOoYwDHUG8Nl18nOQRF"
# shouldn't be public but not too concerned given project scope
API_CLIENT_SECRET = "ZZIFNkc3CPRJ6LKvnJPZDKtIOIMzAyF6rWTaDJcRCazIAevkRMdy5jMGjr5sHIt0" 
THING_ID          = "2964b461-851a-45fd-a2e4-93aea1ce8d0f"
TOKEN_URL         = "https://api2.arduino.cc/iot/v1/clients/token"

client = BackendApplicationClient(client_id=API_CLIENT_ID)
oauth  = OAuth2Session(client=client)
token  = oauth.fetch_token(
    token_url=TOKEN_URL,
    client_id=API_CLIENT_ID,
    client_secret=API_CLIENT_SECRET,
    include_client_id=True,
    audience="https://api2.arduino.cc/iot"
)
print(f"Retrieved access token (len={len(token['access_token'])})\n")

# fetch all available metadata as json
props_resp = oauth.get(f"https://api2.arduino.cc/iot/v1/things/{THING_ID}/properties")
props_resp.raise_for_status()
properties = props_resp.json()

# filter json response to 4 properties
target = {"pH", "temperature", "turbidity", "tds"}
selected = [p for p in properties if p["name"] in target] # selects only properties in the list, can be expanded

# time window for data series, currently set to t-7 days
end   = datetime.now(timezone.utc).isoformat()
start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

# properties client to retrieve property data
cfg       = Configuration(host="https://api2.arduino.cc")
cfg.access_token = token["access_token"]
api_client = ApiClient(cfg)
prop_api    = PropertiesV2Api(api_client)

# retrieve time series data for each prop in properties
for prop in selected:
    resp = prop_api.properties_v2_timeseries(
        id=THING_ID,
        pid=prop["id"],
        var_from=start,
        to=end
    )
    values = getattr(resp, "values", [])
    print(f"{prop['name']} ({len(values)} points):")
    for point in values:
        print(f"  • {point.timestamp} → {point.value}")