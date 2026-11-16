"""TBMM resmî milletvekili listesini (tbmm.gov.tr/milletvekili/AllList) data/tbmm.json'a yazar.
GitHub Actions'ta düzenli çalışır; uygulama isimle aramada bu listeyi kullanır (görevi ve partisiyle).
Liste okunamazsa ya da şüpheli derecede kısaysa eski dosyaya dokunmaz."""
import json, os, re, sys, subprocess, datetime, html
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rehber'))
from tbmm import name_fix, tr_title
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'data', 'tbmm.json')
s = subprocess.run(['curl', '-sL', '-m', '90', '-A', 'Mozilla/5.0', 'https://tbmm.gov.tr/milletvekili/AllList'], capture_output=True, text=True).stdout
mv, il = [], None
for m in re.finditer(r'<li class="list-group-item ([^"]*)"[^>]*>(.*?)</li>', s, re.S):
    cls, body = m.group(1), m.group(2)
    if 'active' in cls:
        il = html.unescape(re.sub(r'<[^>]+>', '', body)).strip(); continue
    a = re.search(r'href="([^"]*)"[^>]*>([^<]+)</a>', body); p = re.search(r'text-right">\s*([^<]+?)\s*</div>', body)
    if a and il:
        mv.append({'n': name_fix(html.unescape(a.group(2)).strip()), 'il': tr_title(il), 'parti': html.unescape(p.group(1)).strip() if p else ''})
if len(mv) < 500:
    print('TBMM listesi okunamadı ya da eksik:', len(mv)); sys.exit(0)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime('%Y-%m-%dT%H:%M')
old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
if old.get('mv') == mv: print('TBMM listesi değişmedi', len(mv)); sys.exit(0)
json.dump({'kaynak': 'tbmm.gov.tr/milletvekili/AllList', 'alindi': now, 'mv': mv}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('TBMM listesi güncellendi', len(mv))
