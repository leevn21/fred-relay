"""GitHub Action -> docs/fred_ext.json: chuoi vi mo bo sung cho module Ban tin thuc chien (4FX).
Cung FRED API + FRED_API_KEY nhu fetch.py; file rieng de khong dung toi docs/fred.json dang dung.
Khong ghi de neu rong."""
import json, os, time, urllib.request

SERIES = [
    "CPIAUCSL", "CPILFESL", "PCEPILFE", "PAYEMS", "UNRATE", "A191RL1Q225SBEA", "CES0500000003",
    "JTSJOL", "RSAFS", "MICH", "ICSA", "DFEDTARU", "DGS2", "DGS10", "INDPRO", "UMCSENT",
    "JPNCPIALLMINMEI", "LRUN64TTJPM156S", "CANCPIALLMINMEI", "LRUNTTTTCAM156S", "CHECPIALLMINMEI",
    "AUSCPIALLQINMEI", "NZLCPIALLQINMEI",
]
START = "1990-01-01"
KEY = os.environ.get("FRED_API_KEY", "").strip()


def fetch_one(sid):
    u = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=%s"
         "&file_type=json&observation_start=%s" % (sid, KEY, START))
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    out = []
    for o in json.loads(raw).get("observations", []):
        v = (o.get("value") or "").strip()
        if v in ("", "."):
            continue
        try:
            out.append([int(time.mktime(time.strptime(o["date"], "%Y-%m-%d"))), float(v)])
        except Exception:
            continue
    return out


if not KEY:
    print("THIEU FRED_API_KEY"); raise SystemExit(1)
data = {"updated": int(time.time()), "cosd": START, "series": {}}
total = 0
for sid in SERIES:
    try:
        pts = fetch_one(sid); data["series"][sid] = pts; total += len(pts)
        print("OK %s: %d diem" % (sid, len(pts)))
    except Exception as e:
        print("LOI %s: %s" % (sid, str(e)[:100])); data["series"][sid] = []
    time.sleep(0.6)
if total == 0:
    print("TAT CA RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/fred_ext.json", "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
print("Da ghi docs/fred_ext.json - total=%d" % total)
