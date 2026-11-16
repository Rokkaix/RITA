"""Resmî kaynak listelerini RITA rehberiyle karşılaştırıp güncelleme paketi (data/rehber.json) üretir.
Kullanım: python3 tools/rehber/derle.py  (index.html içindeki mevcut rehberi okur)"""
import json, re, os, unicodedata, datetime
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = os.path.join(R, 'data', 'rehber-kaynak')
s = open(os.path.join(R, 'index.html'), encoding='utf-8').read()
def arr(name):
    i = s.index(name + '=['); return json.JSONDecoder().raw_decode(s[i + len(name) + 1:])[0]
K0 = arr('K0')
def norm(t):
    t = (t or '').replace('İ', 'i').replace('I', 'ı').lower()
    t = t.translate(str.maketrans('şğüöçı', 'sguoci'))
    t = unicodedata.normalize('NFD', t); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', t)).strip()
def nk(n):
    return re.sub(r'\s+', ' ', re.sub(r'\b(prof|doc|dr|av|op|uzm|ing|org|korg|tumg|tugg|oramiral|koramiral|tumamiral|tuggeneral|tumgeneral|korgeneral|orgeneral)\b\.?', ' ', norm(n))).strip()
by = {}
for x in K0: by.setdefault(nk(x[0]), []).append(x)
ekle, guncelle, eskit = [], [], []
def cur_title(x): return x[1]
def add_or_update(n, role, r, u, kat, match_re):
    k = nk(n)
    if k in by:
        x = by[k][0]
        if not re.search(match_re, norm(x[1])) or re.search(r'\beski\b', norm(x[1].split(' · ')[0])) and re.search(match_re, norm(x[1].split(' · ')[0])):
            parts = [p for p in x[1].split(' · ') if not re.search(match_re, norm(p))]
            t_new = ' · '.join([role] + parts)
            guncelle.append({'n': x[0], 't_old': x[1], 't_new': t_new, 'r': min(x[2], r) if isinstance(x[2], (int, float)) else r, 'u': x[3] or u, 'kat': kat})
    else:
        ekle.append({'n': n, 't': role, 'r': r, 'u': u, 'kat': kat})
# --- Kabine
for p in json.load(open(os.path.join(K, 'kabine.json'), encoding='utf-8')):
    g = p['g']; r, u = (2, 'Cumhurbaşkanlığı Genel Sekreteri ve Eşi') if 'Yardımcısı' in g else (9, 'Bakanlar Kurulu Üyeleri ve Eşleri')
    add_or_update(p['n'], g, r, u, 'Kabine', re.escape(norm(g)))
# --- Milletvekilleri: ad + il + görev uyumuyla eşleştir (ikinci adlar, yazım farkları)
import difflib
MV = json.load(open(os.path.join(K, 'milletvekilleri.json'), encoding='utf-8'))
ACT_BAD = re.compile(r'\b(bakani|valisi|buyukelcisi|cumhurbaskani|genelkurmay|komutani|rektoru|hakimi|savcisi)\b')
def active_segs(t): return [p for p in t.split(' · ') if not re.search(r'\beski\b|\bemekli\b|dogrulayin|donem', norm(p))]
def mp_compatible(x):
    return not any(ACT_BAD.search(norm(p)) for p in active_segs(x[1]))
ILLER = {norm(v['il']) for v in json.load(open(os.path.join(K, 'valiler.json'), encoding='utf-8'))}
def fz(a, b): return difflib.SequenceMatcher(None, a, b).ratio()
def mp_score(x, p):
    """0: farklı kişi, 3: birebir ad, 2: ikinci ad / evlilik soyadı, 1: küçük yazım farkı"""
    a, b = nk(x[0]).split(), nk(p['n']).split()
    if not a or not b: return 0
    il = norm(p['il']); tit = norm(x[1])
    il_in = re.search(r'\b' + re.escape(il) + r'\b', tit) is not None
    has_il = any(re.search(r'\b' + re.escape(i) + r'\b', tit) for i in ILLER)
    if has_il and not il_in: return 0
    if a == b: return 3
    loose = all(any(t == u or fz(t, u) >= 0.8 for u in b) for t in a) and a[-1] == b[-1]
    if loose and len(a) == len(b) and not has_il and 'milletvekili' in tit: return 1   # ili yazılmamış milletvekili, ufak yazım farkı
    if not il_in: return 0          # benzer ad eşleşmesi için il yazılı olmalı
    if loose: return 1
    if set(a) < set(b) and a[-1] == b[-1]: return 2                          # TBMM'de baştaki / ortadaki ad var
    if set(a) < set(b) and a[0] == b[0] and a[-1] in b: return 2           # TBMM'de ikinci ad var
    if set(a) < set(b) and a[0] == b[0] and a[-1] == b[-2]: return 2        # evlilik soyadı eklenmiş
    if len(a) > len(b) and a[:len(b)] == b: return 2                         # rehberde evlilik soyadı fazla
    if len(a) == len(b) and a[0] == b[0] and fz(a[-1], b[-1]) >= 0.8 and fz(' '.join(a), ' '.join(b)) >= 0.85: return 1
    if len(a) == len(b) and a[-1] == b[-1] and fz(a[0], b[0]) >= 0.8: return 1
    return 0
mp_match = {}
for p in MV:
    sc = sorted(((mp_score(x, p), x) for L in by.values() for x in L if mp_compatible(x)), key=lambda t: -t[0])
    mp_match[p['n']] = sc[0][1] if sc and sc[0][0] > 0 else None
matched_ids = {id(x) for x in mp_match.values() if x}
for p in MV:
    role = f"{p['il']} Milletvekili ({p['parti']})"
    x = mp_match[p['n']]
    if not x:
        ekle.append({'n': p['n'], 't': role, 'r': 21, 'u': 'TBMM Üyeleri ve Eşleri', 'kat': 'Milletvekili'}); continue
    segs = x[1].split(' · ')
    keep = [q for q in segs if not re.search(r'\bmilletvekili\b', norm(q)) and norm(q) not in (norm(p['il']),) and not re.fullmatch(r'\d+\. donem', norm(q))]
    t_new = ' · '.join(keep[:1] + [role] + keep[1:]) if keep and not re.search(r'eski', norm(keep[0])) else ' · '.join([role] + keep)
    if norm(t_new) != norm(x[1]):
        guncelle.append({'n': x[0], 't_old': x[1], 't_new': t_new, 'r': min(x[2], 21) if isinstance(x[2], (int, float)) else 21, 'u': x[3] or 'TBMM Üyeleri ve Eşleri', 'kat': 'Milletvekili', 'tam_ad': p['n']})
for k, L in by.items():
    for x in L:
        if id(x) in matched_ids: continue
        segs = x[1].split(' · ')
        act = [q for q in segs if re.search(r'\bmilletvekili\b', norm(q)) and not re.search(r'\beski\b', norm(q))]
        if not act: continue
        # yakın bir isim TBMM listesinde varsa (belirsiz) dokunma
        a = nk(x[0]).split()
        if any(mp_score(x, p) > 0 for p in MV): continue
        t_new = ' · '.join(('Eski ' + q if q in act else q) for q in segs)
        only_mv = all(re.search(r'milletvekili|^[a-z ]+$', norm(q)) for q in active_segs(x[1]))
        eskit.append({'n': x[0], 't_old': x[1], 't_new': t_new, 'r': 21.9 if x[2] == 21 else x[2], 'u': 'TBMM Eski Üyeleri ve Eşleri' if x[3] == 'TBMM Üyeleri ve Eşleri' else x[3], 'kat': 'Milletvekili'})
# --- Valiler
VA = json.load(open(os.path.join(K, 'valiler.json'), encoding='utf-8'))
cur = {norm(v['il']): nk(v['n']) for v in VA}
for v in VA:
    r = 39 if v['il'] == 'Ankara' else 60
    k = nk(v['n']); role = f"{v['il']} Valisi"
    xs = [x for x in by.get(k, []) if not re.search(r'milletvekili', norm(x[1]))]
    if not xs:
        ekle.append({'n': v['n'], 't': role, 'r': r, 'u': 'İl Valileri ve Eşleri', 'kat': 'Vali'}); continue
    x = xs[0]
    if not re.search(r'(?<!eski )\b' + re.escape(norm(v['il'])) + r' valisi\b', norm(x[1])) or re.match(r'eski', norm(x[1])):
        segs = [q for q in x[1].split(' · ') if not re.search(r'valisi', norm(q)) and 'dogrulayin' not in norm(q)]
        guncelle.append({'n': x[0], 't_old': x[1], 't_new': ' · '.join([role] + segs), 'r': r, 'u': 'İl Valileri ve Eşleri', 'kat': 'Vali'})
    elif '(' in x[1] or 'dogrulayin' in norm(x[1]):
        guncelle.append({'n': x[0], 't_old': x[1], 't_new': role, 'r': r, 'u': 'İl Valileri ve Eşleri', 'kat': 'Vali'})
for k, L in by.items():
    for x in L:
        segs = x[1].split(' · ')
        for p in segs:
            m = re.match(r'^(.+?) valisi\b', norm(p))
            if m and not norm(p).startswith('eski') and m.group(1) in cur and cur[m.group(1)] != k:
                t_new = ' · '.join(('Eski ' + q if q == p else q) for q in segs)
                eskit.append({'n': x[0], 't_old': x[1], 't_new': re.sub(r'\s*\(\d\d\.\d\d\.\d{4} kararnamesi\)', '', t_new), 'r': 82 if x[2] in (39, 60) else x[2], 'u': '' if x[3] == 'İl Valileri ve Eşleri' else x[3], 'kat': 'Vali'})
# --- Kaymakamlar (rical listesinde sıra numarası yok; aranabilir kayıt)
for p in json.load(open(os.path.join(K, 'kaymakamlar.json'), encoding='utf-8')):
    if nk(p['n']) not in by:
        ekle.append({'n': p['n'], 't': f"{p['ilce']} Kaymakamı ({p['il']})", 'r': 999, 'u': '', 'kat': 'Kaymakam'})
# aynı kişi iki kez eklenmesin
seen, E2 = set(), []
for e in ekle:
    k = (nk(e['n']), e['t'])
    if k in seen: continue
    seen.add(k); E2.append(e)
out = {'tarih': datetime.date.today().isoformat(),
       'kaynaklar': {'Kabine': 'tccb.gov.tr/kabine', 'Milletvekili': 'tbmm.gov.tr/milletvekili/AllList', 'Vali': 'icisleri.gov.tr/valilikler', 'Kaymakam': 'icisleri.gov.tr il detayları'},
       'ekle': E2, 'guncelle': guncelle, 'eskit': eskit}
json.dump(out, open(os.path.join(R, 'data', 'rehber.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
from collections import Counter
print('ekle', len(E2), Counter(e['kat'] for e in E2)); print('guncelle', len(guncelle), Counter(e['kat'] for e in guncelle)); print('eskit', len(eskit), Counter(e['kat'] for e in eskit))
