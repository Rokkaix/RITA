"""Üniversite rektörleri: Wikipedia 'Türkiye'deki üniversiteler listesi' + her üniversite sayfasının bilgi kutusundaki 'Rektör'.
Kullanım: python3 rektorler.py <liste.html> <önbellek_klasörü>  -> JSON (stdout)"""
import sys, re, json, html, subprocess, os, time, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
def cl(c): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<sup.*?</sup>', '', c, flags=re.S)))).strip()
def get(href, cache):
    f = os.path.join(cache, urllib.parse.unquote(href.split('/wiki/')[-1])[:120].replace('/', '_') + '.html')
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        subprocess.run(['curl', '-sL', '-m', '40', '-A', 'Mozilla/5.0 (RITA rehber)', '-o', f, 'https://tr.wikipedia.org' + urllib.parse.quote(href)]); time.sleep(1.2)
    return open(f, encoding='utf-8', errors='ignore').read() if os.path.exists(f) else ''
UNV = r'^(Prof\.?|Doç\.?|Dr\.?|Av\.?|Ord\.?|Öğr\.?|Üyesi|\s)+'
s = open(sys.argv[1], encoding='utf-8').read()
t = re.search(r'<table class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>', s, re.S).group(1)
out, city = [], ''
for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S)[1:]:
    cells = re.findall(r'<t[dh]([^>]*)>(.*?)</t[dh]>', r, re.S)
    if not cells: continue
    if len(cells) >= 5 or 'rowspan' in cells[0][0]: city = cl(cells[0][1]); cells = cells[1:]
    if len(cells) < 2: continue
    a = re.search(r'href="(?:https://tr.wikipedia.org)?(/wiki/[^"#]+)"', cells[0][1]); ad = cl(cells[0][1]); tur = cl(cells[1][1])
    rek = ''
    if a:
        box = re.search(r'<table class="infobox.*?</table>', get(a.group(1), sys.argv[2]), re.S)
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', box.group(0) if box else '', re.S):
            th = re.search(r'<th[^>]*>(.*?)</th>', row, re.S); td = re.search(r'<td[^>]*>(.*?)</td>', row, re.S)
            if th and td and re.match(r'Rektör', cl(th.group(1))) and 'yardımcı' not in cl(th.group(1)).lower():
                rek = cl(td.group(1)); break
    nm = re.split(r'\s*[\(\[,;]|\s{2,}', re.sub(UNV, '', rek).strip())[0].strip()
    out.append({'uni': ad, 'il': city, 'tur': tur, 'n': name_fix(' '.join(w[0] + w[1:].replace('I', 'ı').replace('İ', 'i').lower() if w.isupper() and len(w) > 1 else w for w in nm.split())) if nm else '', 'ham': rek[:100]})
print(json.dumps(out, ensure_ascii=False, indent=0))
