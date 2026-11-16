"""Yüksek yargı: Yargıtay resmî sitesi (yargitay.gov.tr) yönetim sayfaları -> JSON [{n, t, kurum}].
Kullanım: python3 yargi.py <önbellek_klasörü>"""
import sys, re, json, html, subprocess, os, time
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
C = sys.argv[1]
def get(path):
    f = os.path.join(C, path.replace('/', '_') + '.html')
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        subprocess.run(['curl', '-sL', '-m', '40', '-A', 'Mozilla/5.0', '-o', f, 'https://www.yargitay.gov.tr/category/' + path]); time.sleep(1)
    s = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'<main.*?</main>|<div class="content.*', s, re.S); s = m.group(0) if m else s
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' | ', s)))
    t = re.sub(r'(\| *)+', '| ', t)
    return t.split('| YÖNETİM |')[0]
UNV = r'^(Prof\.|Doç\.|Dr\.|\s)+'
def ad(x): return name_fix(re.sub(UNV, '', x).strip().title() if x.isupper() else re.sub(UNV, '', x).strip())
def ad2(x):  # 'Ömer KERKEZ' -> 'Ömer Kerkez'
    x = re.sub(UNV, '', x).strip()
    return name_fix(' '.join(w if not w.isupper() else w[0] + w[1:].replace('I', 'ı').replace('İ', 'i').lower() for w in x.split()))
out = []
t = get('76/baskan'); m = re.search(r'YARGITAY BAŞKANI \| ([^|]+)\|', t)
if m: out.append({'n': ad2(m.group(1)), 't': 'Yargıtay Başkanı', 'kurum': 'Yargıtay'})
t = get('78/baskan-vekilleri')
for m in re.finditer(r'YARGITAY BAŞKANVEKİLİ \| ([^|]+)\|', t): out.append({'n': ad2(m.group(1)), 't': 'Yargıtay Birinci Başkanvekili', 'kurum': 'Yargıtay'})
t = get('80/daire-baskanlari')
for m in re.finditer(r'\| ([^|]{4,60}?) \| (\d+)\.(Hukuk|Ceza) Dairesi Başkanı', t):
    out.append({'n': ad2(m.group(1)), 't': f"Yargıtay {m.group(2)}. {m.group(3)} Dairesi Başkanı", 'kurum': 'Yargıtay'})
t = get('81/genel-sekreter'); m = re.search(r'Genel Sekreter[iİ]? \| (?:YARGITAY GENEL SEKRETER[İI] \| )?([^|]+)\|', t)
if m: out.append({'n': ad2(m.group(1)), 't': 'Yargıtay Genel Sekreteri', 'kurum': 'Yargıtay'})
print(json.dumps(out, ensure_ascii=False, indent=0))
