"""GitHub Action -> docs/wb.json: World Bank 12 chi so x 106 nuoc (per-nuoc, DA CHAY DUOC).
IN LOI RO + tien do de kiem tra backend. 16 luong. WB API cong khai, khong can key.
Trang lay: https://api.worldbank.org/v2/country/<iso3>/indicator/<code>?date=..&format=json"""
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

# ---- CHAN DOAN: goi thu 1 URL, in nguyen van de biet WB co chan / format dung khong ----
_test = "https://api.worldbank.org/v2/country/VNM/indicator/NY.GDP.MKTP.KD.ZG?date=2020:2024&format=json&per_page=100"
try:
    _raw = urllib.request.urlopen(urllib.request.Request(_test, headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read().decode("utf-8", "ignore")
    print("CHANDOAN OK · do dai=%d · mau: %s" % (len(_raw), _raw[:220]))
except Exception as e:
    print("CHANDOAN LOI (WB co the chan runtime nay): %r" % (str(e)[:200]))

_errs = []


def fetch_one(iso3, code):
    u = "https://api.worldbank.org/v2/country/%s/indicator/%s?date=%d:%d&format=json&per_page=300" % (iso3, code, START, END)
    last = ""
    for _try in range(3):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
            arr = json.loads(raw)
            if not isinstance(arr, list) or len(arr) < 2 or not arr[1]:
                return []
            out = []
            for it in arr[1]:
                v = it.get("value"); yr = it.get("date")
                if v is None or not yr:
                    continue
                try:
                    out.append([iso3, code, int(yr), float(v)])
                except Exception:
                    continue
            return out
        except Exception as e:
            last = str(e)[:80]; time.sleep(2 + _try * 3)
    if last and len(_errs) < 8:
        _errs.append("%s/%s: %s" % (iso3, code, last))
    return []


tasks = [(iso, c) for iso in ISO3 for c in INDS]
rows = []
done = 0
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = [ex.submit(fetch_one, iso, c) for iso, c in tasks]
    for fu in as_completed(futs):
        done += 1
        try:
            rows += fu.result() or []
        except Exception:
            pass
        if done % 300 == 0:
            print("  ... %d/%d task · %d dong" % (done, len(tasks), len(rows)))

print("XONG · tong dong: %d / %d task" % (len(rows), len(tasks)))
for e in _errs:
    print("  LOI mau:", e)
if not rows:
    # WB dang loi (vd 502 Bad Gateway tu server WB) -> KHONG lam fail workflow, giu wb.json cu,
    # de FRED van commit binh thuong; cron lan sau tu thu lai khi WB hoi.
    print("RONG (WB co the dang 502/sap) -> GIU wb.json cu, khong ghi de. Cron sau tu thu lai.")
    raise SystemExit(0)
os.makedirs("docs", exist_ok=True)
with open("docs/wb.json", "w", encoding="utf-8") as f:
    json.dump({"updated": int(time.time()), "rows": rows}, f, separators=(",", ":"))
print("Da ghi docs/wb.json — rows=%d" % len(rows))
