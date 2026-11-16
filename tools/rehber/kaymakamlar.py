"""İçişleri Bakanlığı il detayları (ValilikDetay, cKey 1..81) -> tüm kaymakamlar JSON."""
import sys, re, json, html, subprocess, os, time
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
out = []
for k in range(1, 82):
    s = subprocess.run(['curl', '-s', '-m', '40', '-A', 'Mozilla/5.0', '-X', 'POST', '-H', 'Content-Type: application/json',
                        '-d', json.dumps({'cKey': k}), 'https://www.icisleri.gov.tr/ISAYWebPart/Valilikler/ValilikDetay'], capture_output=True, text=True).stdout
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' | ', s)))
    il = re.search(r"locations = \[ \['([^']+?) Valiliği'", t)
    il = il.group(1) if il else str(k)
    for m in re.finditer(r"\| ([^|]+?) \| \| \| \| \| Kaymakam \| \| ([^|]+?) \|", t):
        n = m.group(2).strip()
        if n and n not in ('-',):
            out.append({'il': il, 'ilce': m.group(1).strip(), 'n': name_fix(n)})
    time.sleep(0.4)
print(json.dumps(out, ensure_ascii=False, indent=0))
