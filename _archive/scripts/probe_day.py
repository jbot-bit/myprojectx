import os, datetime as dt
from zoneinfo import ZoneInfo
import httpx
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PROJECTX_BASE_URL","").strip()
USER = os.getenv("PROJECTX_USERNAME","").strip()
KEY  = os.getenv("PROJECTX_API_KEY","").strip()
LIVE = os.getenv("PROJECTX_LIVE","false").lower() in ("1","true","yes","y")
TZ_LOCAL = ZoneInfo(os.getenv("TZ_LOCAL","Australia/Brisbane"))

CONTRACT_ID = "CON.F.US.MGC.G26"

def day_window(d: dt.date):
    s_local = dt.datetime(d.year,d.month,d.day,0,0,tzinfo=TZ_LOCAL)
    e_local = s_local + dt.timedelta(days=1)
    s = s_local.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z")
    e = e_local.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z")
    return s,e

def headers(tok=None):
    h={"accept":"text/plain","Content-Type":"application/json"}
    if tok: h["Authorization"]=f"Bearer {tok}"
    return h

d = dt.date.fromisoformat(os.sys.argv[1])
s,e = day_window(d)

with httpx.Client(timeout=60.0) as c:
    tok = c.post(f"{BASE}/api/Auth/loginKey", headers=headers(), json={"userName":USER,"apiKey":KEY}).json()["token"]
    r = c.post(
        f"{BASE}/api/History/retrieveBars",
        headers=headers(tok),
        json={
            "contractId": CONTRACT_ID,
            "live": LIVE,
            "startTime": s,
            "endTime": e,
            "unit": 2,
            "unitNumber": 1,
            "limit": 20000,
            "includePartialBar": False
        }
    )
    r.raise_for_status()
    j = r.json()
    bars = j.get("bars") or []
    print("success:", j.get("success"), "bars:", len(bars))
    if bars:
        print("first t:", bars[0]["t"])
        print("last  t:", bars[-1]["t"])
