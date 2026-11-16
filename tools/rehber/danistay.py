"""Danıştay yönetimi: danistay.gov.tr sayfaları tarayıcıyla açılıp içerik yanıtları kaydedilir (menü: danistay.json, içerik: dnall.json).
Kullanım: python3 danistay.py <danistay.json> <dnall.json>  -> JSON [{n, t, kurum}]"""
import sys, re, json, html, os
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
def ad(x):
    x = re.sub(r'^(Prof\.|Doç\.|Dr\.|\s)+', '', x).strip()
    return name_fix(' '.join(w[0] + w[1:].replace('I', 'ı').replace('İ', 'i').lower() if w.isupper() and len(w) > 1 else w for w in x.split()))
SIRA = {'Birinci': 1, 'İkinci': 2, 'Üçüncü': 3, 'Dördüncü': 4, 'Beşinci': 5, 'Altıncı': 6, 'Yedinci': 7, 'Sekizinci': 8, 'Dokuzuncu': 9, 'Onuncu': 10, 'Onbirinci': 11, 'Onikinci': 12, 'Onüçüncü': 13}
menu = {re.search(r'icerik/(\d+)', x['h']).group(1): (x['daire'], x['t']) for x in json.load(open(sys.argv[1], encoding='utf-8'))}
out = []
for k, v in json.load(open(sys.argv[2], encoding='utf-8')).items():
    j = json.loads(v); j = j[0] if isinstance(j, list) else j
    t = re.sub(r'(\s*\|\s*)+', ' | ', html.unescape(re.sub(r'<[^>]+>', ' | ', j.get('icerik', '')))).strip(' |')
    daire, lab = menu.get(k, ('', ''))
    if lab == 'Başkanvekilleri':
        for m in re.finditer(r'Danıştay Başkanvekili \| ([^|]+?) \|', t): out.append({'n': ad(m.group(1)), 't': 'Danıştay Başkanvekili', 'kurum': 'Danıştay'})
        continue
    n = ad(re.sub(r'^(Danıştay [^|]+?) \| ', '', t).split(' | ')[0])
    if lab == 'Başkan' and not daire: role = 'Danıştay Başkanı'
    elif lab == 'Başsavcı': role = 'Danıştay Başsavcısı'
    elif lab == 'Genel Sekreter': role = 'Danıştay Genel Sekreteri'
    elif lab == 'Başkan': role = f'Danıştay {daire} Başkanı'
    else: role = f"Danıştay {SIRA.get(daire.split()[0], daire)}. Daire Başkanı"
    out.append({'n': n, 't': role, 'kurum': 'Danıştay'})
M = {}
for o in out:
    if o['n'] in M: M[o['n']]['t'] += ' · ' + o['t']
    else: M[o['n']] = dict(o)
print(json.dumps(list(M.values()), ensure_ascii=False, indent=0))
