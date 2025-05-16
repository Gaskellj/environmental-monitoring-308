from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import iot_api_client as iot
from iot_api_client.rest import ApiException
from iot_api_client.configuration import Configuration

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from iot_api_client.api.properties_v2_api import PropertiesV2Api
from iot_api_client import ApiClient, Configuration

from datetime import datetime, timedelta


# ——— CONFIGURATION ———
API_CLIENT_ID     = "HbFHAQZDuYdVbrOoYwDHUG8Nl18nOQRF"
API_CLIENT_SECRET = "ZZIFNkc3CPRJ6LKvnJPZDKtIOIMzAyF6rWTaDJcRCazIAevkRMdy5jMGjr5sHIt0"
THING_ID          = "2964b461-851a-45fd-a2e4-93aea1ce8d0f"
TOKEN_URL         = "https://api2.arduino.cc/iot/v1/clients/token"

# ——— GET AN OAUTH2 TOKEN ———
client  = BackendApplicationClient(client_id=API_CLIENT_ID)
oauth   = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url="https://api2.arduino.cc/iot/v1/clients/token",
    client_id=API_CLIENT_ID,
    client_secret=API_CLIENT_SECRET,
    include_client_id=True,
    audience="https://api2.arduino.cc/iot",
    method="POST"   # ← either omit this entirely, or set it to "POST"
)
print(f" Got access token (len={len(token['access_token'])})\n")

response = oauth.get(
    f"https://api2.arduino.cc/iot/v1/things/{THING_ID}/properties"
)

properties = response.json()


# 2) Filter to only the sensors you care about
target_names = {"pH", "temperature", "turbidity", "ads"}
selected = [p for p in properties if p["name"] in target_names]

end   = datetime.utcnow().isoformat() + "Z"
start = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"

config = Configuration(host="https://api2.arduino.cc")
config.access_token = token["access_token"]
client = ApiClient(config)
prop_api = PropertiesV2Api(client)

# 3) Pull time-series for each property
for prop in properties:
    resp = prop_api.properties_v2_timeseries(
        id=THING_ID,
        pid=prop["id"],
        var_from=start,
        to=end
    )
    vals = getattr(resp, "values", [])
    print(f"{prop['name']} ({len(vals)} points):")
    for p in vals:
        print(f"  • {p.timestamp} → {p.value}")