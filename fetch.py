"""GitHub Action -> docs/fred.json qua FRED API chinh thuc (api.stlouisfed.org).
Can API key free (bien moi truong FRED_API_KEY). KHONG ghi de neu rong.

Sua 23/10/2026 — vi sao: lan chay #138 that bai voi 11 dong y het nhau

    LOI WALCL: Expecting value: line 1 column 1 (char 0)
    ... (x11)
    TAT CA RONG -> khong ghi de.

Dong do CHI noi "than tra ve khong phai JSON" chu khong noi MA HTTP, content-type hay vai
chuc byte dau cua than — tuc la khong the biet la khoa sai, bi chan, hay FRED doi gi. Ban cu
nuot het su that do:
  * urlopen() NEM HTTPError cho 4xx/5xx, nen "Expecting value" nghia la HTTP 200 ma than
    KHONG phai JSON (trang chan cua WAF/CDN, than rong, hoac XML).
  * tai lieu loi cua FRED: khoa thieu/sai = 400, qua nhip = 429, khoa = 423, loi may = 500 —
    va than loi co the la text/xml NGAY CA khi xin file_type=json.
Nay moi lan hong deu in: MA HTTP - content-type - 200 byte dau. Va thu lai co cho nghi.
"""
import json, os, time, urllib.error, urllib.request

SERIES = ["WALCL","RRPONTSYD","WTREGEN","M2SL","BAMLH0A0HYM2","BAMLC0A0CM","T10YIE","T10Y2Y","DFII10","ECBASSETSW","JPNASSETS"]
START = "2018-01-01"
KEY = os.environ.get("FRED_API_KEY", "").strip()
LAN_THU = 3                      # 1 lan + 2 lan thu lai
NGHI = [2, 8]                    # giay cho truoc lan thu lai 1, 2
TIMEOUT = 30
UA = "fred-relay/2 (+https://github.com/leevn21/fred-relay)"


def _goi(sid):
    """Mot luot goi. -> (ma_http, content_type, than). Khong nem HTTPError ra ngoai."""
    u = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=%s"
         "&file_type=json&observation_start=%s" % (sid, KEY, START))
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, (r.headers.get("Content-Type") or ""), r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as ex:          # 400 khoa sai · 423 khoa · 429 qua nhip · 5xx
        try:
            than = ex.read().decode("utf-8", "ignore")
        except Exception:
            than = ""
        return ex.code, (ex.headers.get("Content-Type") or "" if ex.headers else ""), than


def _goc(s):
    """Vai chuc byte dau, mot dong, de doc duoc trong nhat ky Action."""
    return " ".join((s or "").split())[:200] or "(than RONG)"


def fetch_one(sid):
    """-> (diem, ly_do_hong). Hong thi diem rong va ly_do noi DU ba thu: ma - kieu - than."""
    cuoi = ""
    for lan in range(LAN_THU):
        try:
            ma, ct, than = _goi(sid)
        except Exception as ex:                   # mang dut, DNS, timeout
            cuoi = "mang hong: %s: %s" % (type(ex).__name__, str(ex)[:90])
            ma = 0
        else:
            # ⚠️ PHAI la TUPLE, khong phai chuoi: `"" in "{["` la True trong Python ⇒ than RONG
            #    se lot qua day roi chet o json.loads, va dong bao loi mat content-type. Rig bat duoc.
            if ma == 200 and than.lstrip()[:1] in ("{", "["):
                try:
                    obs = json.loads(than).get("observations", [])
                except Exception as ex:
                    cuoi = "HTTP 200 nhung JSON hong (%s) | %s" % (str(ex)[:50], _goc(than))
                else:
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
                    return out, ""
            else:
                cuoi = "HTTP %s | %s | %s" % (ma, (ct or "(khong co content-type)"), _goc(than))
        # 400/404 la loi CUA TA (khoa sai, ma sai) — thu lai cung the, dung luon
        if ma in (400, 404):
            break
        if lan + 1 < LAN_THU:
            time.sleep(NGHI[min(lan, len(NGHI) - 1)])
    return [], cuoi


def main():
    """Phan dieu khien. Tach ra de IMPORT duoc file nay ma KHONG chay that — rig can the.
    (Ban cu chay ngay khi import: rig vua import la no goi 11 chuoi ra Internet roi SystemExit.)"""
    if not KEY:
        print("THIEU FRED_API_KEY (chua tao secret?)")
        raise SystemExit(1)
    print("FRED_API_KEY: co, dai %d ky tu" % len(KEY))      # KHONG in khoa — chi do dai, du de biet secret rong/dan nham

    data = {"updated": int(time.time()), "cosd": START, "series": {}}
    total, hong = 0, []
    for sid in SERIES:
        pts, ly_do = fetch_one(sid)
        data["series"][sid] = pts
        total += len(pts)
        if ly_do:
            hong.append((sid, ly_do))
            print("LOI %s: %s" % (sid, ly_do))
        else:
            print("OK %s: %d diem" % (sid, len(pts)))

    if total == 0:
        print("TAT CA RONG -> khong ghi de.")
        # Gop mot dong ket luan: 11 dong giong het nhau thi doc mot dong la du hieu chuyen gi
        kieu = {}
        for _s, l in hong:
            k = l.split("|")[0].strip()
            kieu[k] = kieu.get(k, 0) + 1
        print("TOM TAT: %s" % (" · ".join("%s x%d" % (k, n) for k, n in sorted(kieu.items(), key=lambda x: -x[1])) or "(khong ro)"))
        print("Goi y: HTTP 400 = khoa sai/thieu · 423 = khoa tai khoan · 429 = qua 120 goi/phut · "
              "HTTP 200 ma than la HTML = bi chan o tang CDN/WAF (doi IP chay, hoac xin FRED mo).")
        raise SystemExit(1)

    if hong:
        print("CANH BAO: %d/%d chuoi hong nhung van ghi file (con %d diem)." % (len(hong), len(SERIES), total))
    os.makedirs("docs", exist_ok=True)
    with open("docs/fred.json", "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print("Da ghi docs/fred.json - total=%d" % total)


if __name__ == "__main__":
    main()
