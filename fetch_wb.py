"""GitHub Action -> docs/wb.json: World Bank 12 chi so x 106 nuoc.
TOI UU: gop ~30 nuoc/1 call (country/US;VN;DE;.../indicator/X) -> chi ~48 call (khong 502,
khong bi rate-limit nhu 1272 call le). Song song 8 luong + retry. App map iso3->code2."""
import json, time, os, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

INDS = ["NY.GDP.MKTP.KD.ZG", "NY.GDP.MKTP.CD", "NY.GDP.PCAP.CD", "FP.CPI.TOTL.ZG",
        "SL.UEM.TOTL.ZS", "BN.CAB.XOKA.GD.ZS", "GC.DOD.TOTL.GD.ZS", "NE.EXP.GNFS.ZS",
        "NE.IMP.GNFS.ZS", "NE.CON.GOVT.ZS", "NY.GNS.ICTR.ZS", "SP.POP.TOTL"]
ISO3 = ("USA,CAN,MEX,BRA,ARG,CHL,COL,PER,VEN,ECU,BOL,PRY,URY,CRI,PAN,DOM,GTM,CUB,EMU,DEU,"
        "FRA,ITA,GBR,ESP,NLD,BEL,AUT,CHE,SWE,NOR,DNK,FIN,POL,CZE,HUN,ROU,GRC,PRT,IRL,SVK,"
        "HRV,BGR,SRB,UKR,RUS,TUR,ISL,LUX,LTU,LVA,EST,SVN,CHN,JPN,IND,KOR,IDN,VNM,THA,MYS,"
        "PHL,SGP,HKG,TWN,PAK,BGD,LKA,NPL,KHM,MMR,MNG,KAZ,UZB,AZE,GEO,ARM,SAU,ARE,QAT,KWT,"
        "BHR,OMN,JOR,ISR,LBN,IRQ,IRN,ZAF,EGY,NGA,KEN,MAR,DZA,TUN,GHA,ETH,TZA,UGA,CIV,SEN,"
        "AGO,CMR,ZMB,ZWE,AUS,NZL").split(",")
START, END = 2000, 2025
CHUNKS = [ISO3[i:i + 30] for i in range(0, len(ISO3), 30)]   # ~30 nuoc/call


def fetch_batch(iso_list, code):
    ctys = ";".join(iso_list)
    u = ("https://api.worldbank.org/v2/country/%s/indicator/%s?date=%d:%d&format=json&per_page=20000"
         % (ctys, code, START, END))
    for _ in range(3):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
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
        except Exception:
            time.sleep(2)
    return []


tasks = [(ch, c) for ch in CHUNKS for c in INDS]
rows = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(fetch_batch, ch, c) for ch, c in tasks]
    for fu in as_completed(futs):
        try:
            rows += fu.result() or []
        except Exception:
            pass

print("tong dong: %d (tu %d task = %d chunk x %d chi so)" % (len(rows), len(tasks), len(CHUNKS), len(INDS)))
if not rows:
    print("RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/wb.json", "w", encoding="utf-8") as f:
    json.dump({"updated": int(time.time()), "rows": rows}, f, separators=(",", ":"))
print("Da ghi docs/wb.json — rows=%d" % len(rows))
