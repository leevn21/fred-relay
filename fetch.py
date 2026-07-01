import urllib.request, urllib.error
def probe(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=15)
        return "OK %s len=%d" % (getattr(r,'status',200), len(r.read()))
    except urllib.error.HTTPError as e:
        return "HTTP %d (VAO DUOC!)" % e.code
    except Exception as e:
        return "FAIL: %s" % e

print("api.stlouisfed.org:", probe("https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&file_type=json"))
print("fred graph       :", probe("https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL"))
print("stooq            :", probe("https://stooq.com/q/d/l/?s=fred_walcl&i=d"))
raise SystemExit(1)
