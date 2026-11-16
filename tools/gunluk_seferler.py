"""Her gün: takip edilen hatlardaki THY seferlerini (bugün + yarın) FlightStats'ten alır,
data/rita-veri.json içine "beklemede" kayıt olarak yazar. Onaylı kayda asla dokunmaz."""
import json, os, sys, datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thy_flights import route, aircraft

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, "data", "rita-veri.json")
now = datetime.datetime.now(ZoneInfo("Europe/Istanbul"))
st = json.load(open(P, encoding="utf-8"))
st.setdefault("seferler", {})
key = lambda L: sorted((u.get("hat", "IST-ESB"), u["no"], u["kalkis"], u.get("tip", "")) for u in L)
HATLAR = sorted((st.get("hatlar") or {"IST-ESB": {}}).keys(), key=lambda h: (h != "IST-ESB", h))
changed = False
for day in (now.date(), now.date() + datetime.timedelta(days=1)):
    ucus = []
    for h in HATLAR:
        dep, arr = h.split("-")
        for f in route(day, dep, arr):
            a = aircraft(f) or {}
            ucus.append({"no": f["no"], "hat": h, "kalkis": f["dep"], "inis": f["arr"], "tip": a.get("iata") or "", "ad": ""})
    if not ucus:
        print(day, "sefer bulunamadı"); continue
    ucus.sort(key=lambda u: (u["kalkis"], u["hat"]))
    doc = {"tarih": day.isoformat(), "kaynak": "FlightStats", "alindi": now.strftime("%Y-%m-%dT%H:%M"),
           "durum": "beklemede", "ekleyen": "gunluk-tarama", "ucuslar": ucus}
    did = "gun-" + day.isoformat()
    # bu gün için en son kayıt (aynı gün birden çok kayıt olabilir)
    same = sorted([(k, v) for k, v in st["seferler"].items() if v.get("tarih") == day.isoformat()],
                  key=lambda kv: (kv[1].get("alindi", ""), kv[0]))
    last = same[-1][1] if same else None
    if last and key(last.get("ucuslar", [])) == key(ucus):
        print(day, "değişiklik yok"); continue
    if last and last.get("durum") == "beklemede":
        k = same[-1][0]; st["seferler"][k]["ucuslar"] = ucus; st["seferler"][k]["alindi"] = doc["alindi"]
    elif last:
        st["seferler"][did + "-" + now.strftime("%H%M")] = doc
    else:
        st["seferler"][did] = doc
    changed = True
    print(day, "yeni/güncel kayıt:", len(ucus), "sefer")
# 10 günden eski kayıtları temizle
cut = (now.date() - datetime.timedelta(days=10)).isoformat()
for k in [k for k, v in st["seferler"].items() if v.get("tarih", "9") < cut]:
    del st["seferler"][k]; changed = True
if changed:
    st["guncelleme"] = now.isoformat(timespec="minutes")
    json.dump(st, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("değişti" if changed else "aynı")
