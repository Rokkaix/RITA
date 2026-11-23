"""İstanbul Havalimanı'ndan (IST) kalkan VE İstanbul'a gelen TÜM THY uçuşlarını (iç + dış hat) FlightStats'ten toplar.
Yakın uçuşlar için canlı durum (planlandı/havada/indi/iptal), gecikme, tahmini saat, kapı ve bagaj bandı da alınır.
Şu andan 3 saat öncesi ile 12 saat sonrası arasını tutar; uçak tipini uçuş yaklaştıkça yeniler.
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
    end = now + datetime.timedelta(hours=12)
    while t <= end + datetime.timedelta(hours=6):
        b = (t.date(), (t.hour // 6) * 6)
        if b not in seen:
            seen.append(b)
        t += datetime.timedelta(hours=6)
    return [b for b in seen if datetime.datetime(b[0].year, b[0].month, b[0].day, b[1], tzinfo=TZ) <= end]

found = {}
for yon, sayfa in (("gidis", "departures"), ("gelis", "arrivals")):
  for day, hour in buckets():
    d = next_data(get(f"https://www.flightstats.com/v2/flight-tracker/{sayfa}/IST/?year={day.year}&month={day.month}&date={day.day}&hour={hour}"))
    if not d:
        print("sayfa okunamadı", sayfa, day, hour); continue
    for f in d["props"]["initialState"]["flightTracker"]["route"].get("flights") or []:
        c = f.get("carrier") or {}
        if c.get("fs") != "TK" or f.get("isCodeshare"):
            continue
        if c.get("flightNumber", "").isdigit() and 6000 <= int(c["flightNumber"]) <= 6999:
            continue  # kargo uçuşları
        dep = datetime.datetime.fromisoformat(f["sortTime"].replace("Z", "+00:00")).astimezone(TZ)
        ap = f.get("airport") or {}
        no = "TK" + c["flightNumber"]
        diger = (ap.get("fs") or "???")
        if yon == "gidis":
            fid = no + "-" + dep.strftime("%Y%m%d")
            found[fid] = {"no": no, "yon": "gidis", "hat": "IST-" + diger, "sehir": ap.get("city") or "",
                          "kalkis": f["departureTime"]["time24"], "inis": f["arrivalTime"]["time24"],
                          "zaman": dep.isoformat(timespec="minutes"), "url": f.get("url")}
        else:   # geliş: zaman = İstanbul'a iniş; anahtar saatı iniş saati
            fid = no + "-G-" + dep.strftime("%Y%m%d")
            found[fid] = {"no": no, "yon": "gelis", "hat": diger + "-IST", "sehir": ap.get("city") or "",
                          "kalkis": f["arrivalTime"]["time24"], "dep_saat": f["departureTime"]["time24"], "inis": f["arrivalTime"]["time24"],
                          "zaman": dep.isoformat(timespec="minutes"), "url": f.get("url")}
    time.sleep(0.5)

DURUM = {"S": "Planlandı", "A": "Havada", "L": "İndi", "C": "İptal", "D": "Yönlendirildi", "R": "Yönlendirildi", "U": "Bilinmiyor", "NO": "Uçmadı"}
lo, hi = now - datetime.timedelta(hours=3), now + datetime.timedelta(hours=12)
out, checked = {}, 0
# önce kalkmamış ve en yakın uçuşlar
order = sorted(found.items(), key=lambda kv: (datetime.datetime.fromisoformat(kv[1]["zaman"]) < now, kv[1]["zaman"]))
for fid, f in order:
    dep = datetime.datetime.fromisoformat(f["zaman"])
    if not (lo <= dep <= hi):
        continue
    o = old.get(fid, {})
    rec = {k: v for k, v in f.items() if k != "url"}
    for k in ("tip", "ad", "kontrol", "onceki_tip", "degisti", "durum", "durum_kod", "gecikme", "tahmini", "kapi", "terminal", "bant", "durum_zaman"):
        if k in o:
            rec[k] = o[k]
    last = datetime.datetime.fromisoformat(o["kontrol"]) if o.get("kontrol") else None
    lastd = datetime.datetime.fromisoformat(o["durum_zaman"]) if o.get("durum_zaman") else None
    due_tip = dep > now and ((last is None) or (dep - now < datetime.timedelta(hours=12) and now - last > datetime.timedelta(minutes=110)))
    # canlı durum: -2 saat .. +4 saat penceresindeki uçuşlar, en geç 12 dakikada bir
    due_dr = (now - datetime.timedelta(hours=2) <= dep <= now + datetime.timedelta(hours=4)) and (lastd is None or now - lastd > datetime.timedelta(minutes=12))
    if (due_tip or due_dr) and f.get("url") and checked < 260:
        d = next_data(get("https://www.flightstats.com/v2" + f["url"]))
        checked += 1
        try:
            F = d["props"]["initialState"]["flightTracker"]["flight"]
            eq = (F.get("additionalFlightInfo") or {}).get("equipment") or {}
            tip = eq.get("iata") or ""
            if tip:
                if rec.get("tip") and rec["tip"] != tip:
                    rec["onceki_tip"] = rec["tip"]; rec["degisti"] = now.isoformat(timespec="minutes")
                rec["tip"] = tip; rec["ad"] = eq.get("name") or ""
            tescil = (((F.get("positional") or {}).get("flexTrack") or {}).get("tailNumber") or "").upper()
            if tescil:
                rec["tescil"] = tescil
            rec["kontrol"] = now.isoformat(timespec="minutes")
            st = F.get("status") or {}
            istS = F.get("departureAirport") if f["yon"] == "gidis" else F.get("arrivalAirport")
            istS = istS or {}
            dl = ((st.get("delay") or {}).get("departure" if f["yon"] == "gidis" else "arrival") or {}).get("minutes") or 0
            ea = ((istS.get("times") or {}).get("estimatedActual") or {})
            rec.update(durum_kod=st.get("statusCode") or "", durum=DURUM.get(st.get("statusCode") or "", st.get("status") or ""),
                       gecikme=int(dl or 0), tahmini=ea.get("time24") or "", tahmini_tur=ea.get("title") or "",
                       kapi=istS.get("gate") or "", terminal=istS.get("terminal") or "", bant=istS.get("baggage") or "",
                       durum_zaman=now.isoformat(timespec="minutes"))
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
