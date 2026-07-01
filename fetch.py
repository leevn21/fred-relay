import json, time, csv, io, urllib.request, os

SERIES = ["WALCL","RRPONTSYD","WTREGEN","M2SL","BAMLH0A0HYM2","BAMLC0A0CM","T10YIE","T10Y2Y"]
COSD = "2018-01-01"
UA = {"User-Agent": "Mozilla/5.0 (fred-relay)"}

def fetch_one(sid):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=%s" % (sid, COSD)
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    out = []
    rdr = csv.reader(io.StringIO(raw)); next(rdr, None)
    for row in rdr:
        if len(row) < 2 or not row[0].strip():
            continue
        v = row[1].strip()
        if v in ("", ".", "NA"):
            continue
        try:
            ts = int(time.mktime(time.strptime(row[0].strip(), "%Y-%m-%d")))
            out.append([ts, float(v)])
        except Exception:
            continue
    return out

data = {"updated": int(time.time()), "cosd": COSD, "series": {}}
for sid in SERIES:
    try:
        pts = fetch_one(sid)
        data["series"][sid] = pts
        print("OK %s: %d diem" % (sid, len(pts)))
    except Exception as e:
        print("LOI %s: %s" % (sid, e))
        data["series"][sid] = []

os.makedirs("docs", exist_ok=True)
with open("docs/fred.json", "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
print("Da ghi docs/fred.json (%d chuoi)" % len(data["series"]))
