"""İstanbul Havalimanı'ndan (IST) kalkan TÜM THY uçuşlarını (iç + dış hat) FlightStats'ten toplar.
Şu andan 3 saat öncesi ile 8 saat sonrası arasını tutar; uçak tipini uçuş yaklaştıkça yeniler.
Sonucu data/ucuslar.json dosyasına yazar. Her 30 dakikada bir GitHub'da çalışır."""
import json, os, sys, time, datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thy_flights import get, next_data

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, "data", "ucuslar.json")
TZ = ZoneInfo("Europe/Istanbul")
UTC = datetime.timezone.utc
now = datetime.datetime.now(TZ)
old = {}
try:
    old = json.load(open(P, encoding="utf-8")).get("ucuslar", {})
except Exception:
    pass

def buckets():
    seen = []
    t = now - datetime.timedelta(hours=1)
    end = now + datetime.timedelta(hours=8)
    while t <= end + datetime.timedelta(hours=6):
        b = (t.date(), (t.hour // 6) * 6)
        if b not in seen:
            seen.append(b)
        t += datetime.timedelta(hours=6)
    return [b for b in seen if datetime.datetime(b[0].year, b[0].month, b[0].day, b[1], tzinfo=TZ) <= end]

found = {}
for day, hour in buckets():
    d = next_data(get(f"https://www.flightstats.com/v2/flight-tracker/departures/IST/?year={day.year}&month={day.month}&date={day.day}&hour={hour}"))
    if not d:
        print("sayfa okunamadı", day, hour); continue
    for f in d["props"]["initialState"]["flightTracker"]["route"].get("flights") or []:
        c = f.get("carrier") or {}
        if c.get("fs") != "TK" or f.get("isCodeshare"):
            continue
        if c.get("flightNumber", "").isdigit() and 6000 <= int(c["flightNumber"]) <= 6999:
            continue  # kargo uçuşları
        dep = datetime.datetime.fromisoformat(f["sortTime"].replace("Z", "+00:00")).astimezone(TZ)
        ap = f.get("airport") or {}
        no = "TK" + c["flightNumber"]
        fid = no + "-" + dep.strftime("%Y%m%d")
        found[fid] = {"no": no, "hat": "IST-" + (ap.get("fs") or "???"), "sehir": ap.get("city") or "",
                      "kalkis": f["departureTime"]["time24"], "inis": f["arrivalTime"]["time24"],
                      "zaman": dep.isoformat(timespec="minutes"), "url": f.get("url")}
    time.sleep(0.5)

lo, hi = now - datetime.timedelta(hours=3), now + datetime.timedelta(hours=8)
out, checked = {}, 0
# önce kalkmamış ve en yakın uçuşlar
order = sorted(found.items(), key=lambda kv: (datetime.datetime.fromisoformat(kv[1]["zaman"]) < now, kv[1]["zaman"]))
for fid, f in order:
    dep = datetime.datetime.fromisoformat(f["zaman"])
    if not (lo <= dep <= hi):
        continue
    o = old.get(fid, {})
    rec = {k: v for k, v in f.items() if k != "url"}
    for k in ("tip", "ad", "kontrol", "onceki_tip", "degisti"):
        if k in o:
            rec[k] = o[k]
    last = datetime.datetime.fromisoformat(o["kontrol"]) if o.get("kontrol") else None
    due = dep > now and ((last is None) or (dep - now < datetime.timedelta(hours=7) and now - last > datetime.timedelta(minutes=110)))
    if due and f.get("url") and checked < 200:
        d = next_data(get("https://www.flightstats.com/v2" + f["url"]))
        checked += 1
        try:
            eq = d["props"]["initialState"]["flightTracker"]["flight"]["additionalFlightInfo"]["equipment"]
            tip = eq.get("iata") or ""
            if tip:
                if rec.get("tip") and rec["tip"] != tip:
                    rec["onceki_tip"] = rec["tip"]; rec["degisti"] = now.isoformat(timespec="minutes")
                rec["tip"] = tip; rec["ad"] = eq.get("name") or ""
            rec["kontrol"] = now.isoformat(timespec="minutes")
        except Exception:
            pass
        time.sleep(0.3)
    out[fid] = rec
out = dict(sorted(out.items(), key=lambda kv: kv[1]["zaman"]))

if not out and old:
    print("hiç uçuş bulunamadı; eski veri korunuyor"); sys.exit(0)
json.dump({"guncelleme": now.isoformat(timespec="minutes"), "kaynak": "FlightStats", "kalkis": "IST", "ucuslar": out},
          open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out), "uçuş;", checked, "uçak tipi kontrolü;", sum(1 for r in out.values() if r.get("tip")), "tipi bilinen")
