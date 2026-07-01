"""GitHub Action -> docs/wb.json: World Bank 12 chi so x 106 nuoc.
Goi TUNG nuoc x chi so (query NHO, WB chiu duoc) + SONG SONG 12 luong + retry.
(country/all&per_page lon bi 502/timeout nen dung cach nay — giong app.)"""
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


def fetch_one(iso3, code):
    u = ("https://api.worldbank.org/v2/country/%s/indicator/%s?date=%d:%d&format=json&per_page=300"
         % (iso3, code, START, END))
    for _ in range(2):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
            arr = json.loads(raw)
            if not isinstance(arr, list) or len(arr) < 2 or not arr[1]:
                return []
            out = []
            for it in arr[1]:
                v = it.get("value")
                yr = it.get("date")
                if v is None or not yr:
                    continue
                try:
                    out.append([iso3, code, int(yr), float(v)])
                except Exception:
                    continue
            return out
        except Exception:
            time.sleep(1)
    return []


tasks = [(iso, c) for iso in ISO3 for c in INDS]
rows = []
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(fetch_one, iso, c) for iso, c in tasks]
    for fu in as_completed(futs):
        try:
            rows += fu.result() or []
        except Exception:
            pass

print("tong dong: %d (tu %d task)" % (len(rows), len(tasks)))
if not rows:
    print("RONG -> khong ghi de."); raise SystemExit(1)
os.makedirs("docs", exist_ok=True)
with open("docs/wb.json", "w", encoding="utf-8") as f:
    json.dump({"updated": int(time.time()), "rows": rows}, f, separators=(",", ":"))
print("Da ghi docs/wb.json — rows=%d" % len(rows))
