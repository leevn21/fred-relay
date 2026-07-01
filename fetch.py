import json, urllib.request
def g(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=20).read().decode("utf-8","ignore")

print("=== có provider FRED? ===")
try:
    j = g("https://api.db.nomics.world/v22/providers")
    print("FRED xuat hien:", ('"FRED"' in j))
except Exception as e:
    print("loi providers:", e)

print("=== search WALCL (raw 1500 ky tu) ===")
try:
    print(g("https://api.db.nomics.world/v22/search?q=WALCL&limit=5")[:1500])
except Exception as e:
    print("loi search:", e)

print("=== thu M2 (M2SL) ===")
try:
    print(g("https://api.db.nomics.world/v22/search?q=M2SL&limit=3")[:800])
except Exception as e:
    print("loi:", e)

raise SystemExit(1)
