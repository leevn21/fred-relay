"""GitHub Action -> docs/wb.json: World Bank cho 12 chi so, TAT CA nuoc.
Nhanh: 1 call/chi so (country/all) thay vi 742 request. App map iso3->code2 + wb_code->ten."""
import json, time, os, urllib.request

INDS = ["NY.GDP.MKTP.KD.ZG", "NY.GDP.MKTP.CD", "NY.GDP.PCAP.CD", "FP.CPI.TOTL.ZG",
        "SL.UEM.TOTL.ZS", "BN.CAB.XOKA.GD.ZS", "GC.DOD.TOTL.GD.ZS", "NE.EXP.GNFS.ZS",
        "NE.IMP.GNFS.ZS", "NE.CON.GOVT.ZS", "NY.GNS.ICTR.ZS", "SP.POP.TOTL"]
START, END = 2000, 2025


def fetch_ind(code):
    u = ("https://api.worldbank.org/v2/country/all/indicator/%s?date=%d:%d&format=json&per_page=20000"
         % (code, START, END))
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "ignore")
    arr = json.loads(raw)
    if not isinstance(arr, list) or len(arr) < 2 or not arr[1]:
        return []
    out = []
    for it in arr[1]:
        v = it.get("value")
        iso3 = (it.get("countryiso3code") or "").strip()
        yr = it.get("date")
        if v is None or not iso3 or not yr:
            continue
        try:
            out.append([iso3, code, int(yr), float(v)])
        except Exception:
            continue
    return out


rows = []
for code in INDS:
    try:
        r = fetch_ind(code); rows += r; print("OK %s: %d diem" % (code, len(r)))
    except Exception as e:
        print("LOI %s: %s" % (code, str(e)[:100]))

if not rows:
    print("RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/wb.json", "w", encoding="utf-8") as f:
    json.dump({"updated": int(time.time()), "rows": rows}, f, separators=(",", ":"))
print("Da ghi docs/wb.json — rows=%d" % len(rows))
