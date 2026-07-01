"""GitHub Action -> docs/fred.json qua FRED API chinh thuc (can FRED_API_KEY)."""
import json, time, os, urllib.request

SERIES = ["WALCL","RRPONTSYD","WTREGEN","M2SL","BAMLH0A0HYM2","BAMLC0A0CM","T10YIE","T10Y2Y"]
START = "2018-01-01"
KEY = os.environ.get("FRED_API_KEY", "").strip()

def fetch_one(sid):
    u = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=%s"
         "&file_type=json&observation_start=%s" % (sid, KEY, START))
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    obs = json.loads(raw).get("observations", [])
    out = []
    for o in obs:
        v = (o.get("value") or "").strip()
        if v in ("", "."):
            continue
        try:
            ts = int(time.mktime(time.strptime(o["date"], "%Y-%m-%d")))
            out.append([ts, float(v)])
        except Exception:
            continue
    return out

if not KEY:
    print("THIEU FRED_API_KEY (chua tao secret?)"); raise SystemExit(1)

data = {"updated": int(time.time()), "cosd": START, "series": {}}
total = 0
for sid in SERIES:
    try:
        pts = fetch_one(sid); data["series"][sid] = pts; total += len(pts)
        print("OK %s: %d diem" % (sid, len(pts)))
    except Exception as e:
        print("LOI %s: %s" % (sid, str(e)[:100])); data["series"][sid] = []

if total == 0:
    print("TAT CA RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/fred.json", "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
print("Da ghi docs/fred.json — total=%d" % total)
