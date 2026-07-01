"""GitHub Action -> docs/fred.json. Thu FRED (UA trinh duyet); rong thi lay DBnomics."""
import json, time, csv, io, os, urllib.request

SERIES = ["WALCL","RRPONTSYD","WTREGEN","M2SL","BAMLH0A0HYM2","BAMLC0A0CM","T10YIE","T10Y2Y"]
COSD = "2018-01-01"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def _get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")

def from_fred(sid):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=%s" % (sid, COSD)
    hd = {"User-Agent": UA, "Accept": "text/csv,*/*", "Accept-Language": "en-US,en;q=0.9",
          "Referer": "https://fred.stlouisfed.org/"}
    raw = _get(url, hd, 30); out = []
    rdr = csv.reader(io.StringIO(raw)); next(rdr, None)
    for row in rdr:
        if len(row) < 2 or not row[0].strip(): continue
        v = row[1].strip()
        if v in ("", ".", "NA"): continue
        try:
            ts = int(time.mktime(time.strptime(row[0].strip(), "%Y-%m-%d"))); out.append([ts, float(v)])
        except Exception: continue
    return out

def _dbn_id(sid):
    j = json.loads(_get("https://api.db.nomics.world/v22/search?q=%s&limit=30" % sid, timeout=25))
    docs = (j.get("results") or {}).get("docs") or j.get("docs") or []
    for d in docs:
        if d.get("provider_code") == "FRED" and d.get("series_code") == sid:
            return d.get("series_id") or "FRED/%s/%s" % (d.get("dataset_code"), sid)
    for d in docs:
        if d.get("series_code") == sid and d.get("series_id"): return d["series_id"]
    return None

def from_dbnomics(sid):
    sidd = _dbn_id(sid)
    if not sidd: raise RuntimeError("khong tim thay id")
    j = json.loads(_get("https://api.db.nomics.world/v22/series/%s?observations=1" % sidd, timeout=25))
    docs = (j.get("series") or {}).get("docs") or []
    if not docs: raise RuntimeError("rong")
    out = []
    for p, v in zip(docs[0].get("period") or [], docs[0].get("value") or []):
        if v is None or v == "NA": continue
        try:
            ts = int(time.mktime(time.strptime(str(p)[:10], "%Y-%m-%d"))); out.append([ts, float(v)])
        except Exception: continue
    return out

data = {"updated": int(time.time()), "cosd": COSD, "series": {}}
total = 0
for sid in SERIES:
    pts = []
    try:
        pts = from_fred(sid); print("FRED OK %s: %d" % (sid, len(pts)))
    except Exception as e:
        print("FRED loi %s: %s -> DBnomics" % (sid, str(e)[:50]))
    if not pts:
        try:
            pts = from_dbnomics(sid); print("DBNOMICS OK %s: %d" % (sid, len(pts)))
        except Exception as e:
            print("DBnomics loi %s: %s" % (sid, str(e)[:70]))
    data["series"][sid] = pts; total += len(pts)

if total == 0:
    print("TAT CA RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/fred.json", "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
print("Da ghi docs/fred.json — total=%d" % total)
