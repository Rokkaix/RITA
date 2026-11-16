"""81 il belediye başkanı: Wikipedia'daki '{İl} Büyükşehir Belediyesi' / '{İl} Belediyesi' sayfalarının bilgi kutusundan.
Kullanım: python3 belediye.py <valiler.json> <önbellek_klasörü>  -> JSON (stdout)"""
import sys, re, json, html, subprocess, os, time, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
BB = {'Adana','Ankara','Antalya','Aydın','Balıkesir','Bursa','Denizli','Diyarbakır','Erzurum','Eskişehir','Gaziantep','Hatay',
      'Mersin','İstanbul','İzmir','Kahramanmaraş','Kayseri','Kocaeli','Konya','Malatya','Manisa','Mardin','Muğla','Ordu',
      'Sakarya','Samsun','Şanlıurfa','Tekirdağ','Trabzon','Van'}
def cl(c): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<sup.*?</sup>', '', c, flags=re.S)))).strip()
def get(title, cache):
    f = os.path.join(cache, title.replace(' ', '_') + '.html')
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        u = 'https://tr.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
        subprocess.run(['curl', '-sL', '-m', '40', '-A', 'Mozilla/5.0 (RITA rehber)', '-o', f, u]); time.sleep(1.5)
    return open(f, encoding='utf-8', errors='ignore').read() if os.path.exists(f) else ''
def baskan(s):
    box = re.search(r'<table class="infobox.*?</table>', s, re.S)
    if not box: return None, None
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', box.group(0), re.S):
        th = re.search(r'<th[^>]*>(.*?)</th>', r, re.S); td = re.search(r'<td[^>]*>(.*?)</td>', r, re.S)
        if th and td and re.search(r'[Bb]aşkan|^Lider$', cl(th.group(1))) and not re.search(r'[Yy]ardımcı|[Mm]eclis', cl(th.group(1))):
            return cl(th.group(1)), cl(td.group(1))
    return None, None
il = [x['il'] for x in json.load(open(sys.argv[1]))]
out = []
for p in il:
    t = p + (' Büyükşehir Belediyesi' if p in BB else ' Belediyesi')
    th, td = baskan(get(t, sys.argv[2]))
    if td is None:  # belediye sayfası yoksa şehir sayfasının bilgi kutusu
        t = p; th, td = baskan(get(p if p not in ('Mersin',) else 'Mersin', sys.argv[2]))
    if td is None: out.append({'il': p, 'bb': p in BB, 'n': '', 'ham': '', 'kaynak': t}); continue
    nm = re.split(r'\s*\(|\s{2,}| [A-ZÇĞİÖŞÜ]{2,}[a-z]*\b(?: Parti)?$', td)[0].strip()
    out.append({'il': p, 'bb': p in BB, 'n': name_fix(nm), 'ham': td[:120], 'kaynak': t, 'etiket': th})
print(json.dumps(out, ensure_ascii=False, indent=0))
