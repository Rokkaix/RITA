"""Bir hattaki THY seferlerini (kalkış, iniş, uçak tipi) FlightStats'ten okur.
Kullanım: python3 tools/thy_flights.py IST-ESB [YYYY-MM-DD]"""
import sys, re, json, datetime, subprocess

UA = "Mozilla/5.0"

def get(url):
    r = subprocess.run(["curl", "-sS", "-L", "-m", "30", "-A", UA, url], capture_output=True, text=True)
    return r.stdout

def next_data(html):
    i = html.find("__NEXT_DATA__ = ")
    if i < 0:
        return None
    return json.JSONDecoder().raw_decode(html[i + len("__NEXT_DATA__ = "):])[0]

def route(day, dep="IST", arr="ESB"):
    out = {}
    for hour in (0, 6, 12, 18):
        url = f"https://www.flightstats.com/v2/flight-tracker/route/{dep}/{arr}?year={day.year}&month={day.month}&date={day.day}&hour={hour}"
        d = next_data(get(url))
        if not d:
            continue
        fl = d["props"]["initialState"]["flightTracker"]["route"].get("flights") or []
        for f in fl:
            c = f.get("carrier") or {}
            if c.get("fs") != "TK" or f.get("isCodeshare"):
                continue
            no = "TK" + c["flightNumber"]
            out[no] = {"no": no, "dep": f["departureTime"]["time24"], "arr": f["arrivalTime"]["time24"], "url": f.get("url")}
    return sorted(out.values(), key=lambda x: x["dep"])

def aircraft(f):
    html = get("https://www.flightstats.com/v2" + f["url"])
    d = next_data(html)
    try:
        eq = d["props"]["initialState"]["flightTracker"]["flight"]["additionalFlightInfo"]["equipment"]
        return {"iata": eq.get("iata"), "name": eq.get("name"), "tail": d["props"]["initialState"]["flightTracker"]["flight"]["additionalFlightInfo"].get("tailNumber")}
    except Exception:
        return None

if __name__ == "__main__":
    dep, arr = (sys.argv[1] if len(sys.argv) > 1 else "IST-ESB").split("-")
    day = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
    res = route(day, dep, arr)
    for f in res:
        f["aircraft"] = aircraft(f)
        f.pop("url", None)
    print(json.dumps({"date": day.isoformat(), "source": "FlightStats", "flights": res}, ensure_ascii=False, indent=1))
