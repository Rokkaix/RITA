"""RITA rehberindeki kişiler için DOĞRULANMIŞ portre fotoğrafları -> data/fotolar.json
Kaynak 1: TBMM resmî milletvekili sayfası (isim + il resmî listeden; kimlik kesin).
Kaynak 2: Vikipedi — yalnızca sayfa kişinin BUGÜNKÜ görevini (makam + il/kurum) doğruluyorsa;
          anlam ayrımı, ölmüş adaş ya da görev uyuşmazlığı varsa alınmaz.
Var olan kayıtlar korunur; yalnız eksikler ve 30 günden eskiler yeniden denenir.
Kullanım: python3 tools/fotolar.py [--tbmm] [--viki N]"""
import json, os, re, sys, time, subprocess, datetime, html, unicodedata, urllib.parse
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'data', 'fotolar.json')
sys.path.insert(0, os.path.join(R, 'tools', 'rehber'))
from tbmm import name_fix, tr_title
def get(u, t=40):
    return subprocess.run(['curl', '-sL', '-m', str(t), '-A', 'RITA-rehber-foto/1.0 (https://rokkaix.github.io/RITA/)', u], capture_output=True).stdout.decode('utf-8', 'ignore')
def norm(t):
    t = (t or '').replace('İ', 'i').replace('I', 'ı').lower().translate(str.maketrans('şğüöçı', 'sguoci'))
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', t)).strip()
def nk(n): return re.sub(r'\s+', ' ', re.sub(r'\b(prof|doc|dr|av|op|uzm|ing|org|korg|tumg|tugg|oramiral|koramiral|tumamiral|tuggeneral|tumgeneral|korgeneral|orgeneral)\b\.?', ' ', norm(n))).strip()
DB = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
bugun = datetime.date.today().isoformat()
def kaydet():
    json.dump(dict(sorted(DB.items())), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

def tbmm():
    s = get('https://tbmm.gov.tr/milletvekili/AllList', 90); n = 0
    for m in re.finditer(r'<li class="list-group-item ([^"]*)"[^>]*>(.*?)</li>', s, re.S):
        a = re.search(r'href="(/milletvekili/milletvekilidetay[^"]+)"[^>]*>([^<]+)</a>', m.group(2), re.I)
        if not a: continue
        ad = name_fix(html.unescape(a.group(2)).strip()); k = nk(ad)
        if k in DB and DB[k].get('k') == 'TBMM' and DB[k].get('d', '') > (datetime.date.today() - datetime.timedelta(days=30)).isoformat(): continue
        d = get('https://tbmm.gov.tr' + html.unescape(a.group(1)))
        img = re.search(r'(https://cdn\.tbmm\.gov\.tr/IKBS/Milletvekilleri/Resim/[0-9a-f-]+\.(?:jpe?g|jpe|png))', d, re.I)
        if img:
            DB[k] = {'n': ad, 'u': img.group(1), 'k': 'TBMM', 's': 'tbmm.gov.tr milletvekili sayfası', 'd': bugun}; n += 1
            if n % 40 == 0: kaydet(); print('TBMM', n, flush=True)
        time.sleep(0.3)
    print('TBMM fotoğrafı:', n); kaydet()

GENEL = set('genel muduru mudur baskani baskan baskanligi sekreteri yardimcisi uyesi kurulu kurumu baskanvekili komutani bassavcisi mustesari ve daimi temsilcisi cumhuriyeti turkiye eski emekli birinci ikinci dairesi bakanligi idaresi yuksek'.split())
ROL = [(r'basbakan', 'basbakan'), (r'cumhurbaskani yardimcisi', 'cumhurbaskani yardimcisi'), (r'cumhurbaskani', 'cumhurbaskan'), (r'tbmm baskani|meclis baskani', 'meclis baskan|tbmm baskan'), (r'valisi', 'vali'), (r'bakan yardimcisi', 'bakan yardimcisi'), (r'bakani', 'bakan'), (r'rektoru', 'rektor'), (r'buyukelcisi', 'buyukelci'),
       (r'orgeneral|oramiral', 'orgeneral|oramiral|komutan'), (r'korgeneral|koramiral', 'korgeneral|koramiral|general|amiral'), (r'tumgeneral|tuggeneral|tumamiral|tugamiral', 'general|amiral'),
       (r'komutani', 'komutan'), (r'belediye baskan', 'belediye baskan'), (r'milletvekili', 'milletvekil'), (r'yargitay', 'yargitay'), (r'danistay', 'danistay'),
       (r'anayasa mahkemesi', 'anayasa mahkemesi'), (r'sayistay', 'sayistay'), (r'genel muduru', 'genel mudur'), (r'baskani', 'baskan')]
def dogrula(kisi, unvan, j):
    """Vikipedi özetinin bu kişi ve bu görev olduğunu doğrula."""
    if j.get('type') != 'standard': return 'anlam ayrımı/özel sayfa'
    tit = nk(j.get('title', ''))
    if tit != nk(kisi) and not (set(nk(kisi).split()) <= set(tit.split())): return 'başlık farklı: ' + j.get('title', '')
    metin = norm((j.get('description') or '') + ' ' + (j.get('extract') or ''))
    ham = (j.get('description') or '') + ' ' + (j.get('extract') or '')
    if re.search(r'(?i)\b(öldü|ölümü|vefat)|\(\s*(d\.\s*)?\d{1,2}?\s*\w*\s*\d{4}\s*[-–]\s*\d{1,2}?\s*\w*\s*\d{4}\s*\)|ö\.\s*\d{4}', ham): return 'ölmüş kişi olabilir'
    u = norm(re.sub(r'\s*\(.*?\)', '', unvan.split(' · ')[0]))
    rol = next((r for p, r in ROL if re.search(p, u)), None)
    if not rol or not re.search(rol, metin): return 'görev doğrulanamadı'
    ayirt = [w for w in u.split() if w not in GENEL and len(w) > 2 and not re.search(rol, w)]
    if ayirt and not any(w[:6] in metin for w in ayirt): return 'il/kurum doğrulanamadı'
    return ''

def kisiler():
    src = open(os.path.join(R, 'index.html'), encoding='utf-8').read(); i = src.index('K0=')
    K = json.JSONDecoder().raw_decode(src[i + 3:])[0]
    L = [(x[0], x[1], x[2]) for x in K]
    for f in ('rehber.json', 'rehber-2.json'):
        try:
            P = json.load(open(os.path.join(R, 'data', f), encoding='utf-8'))
            L += [(e['n'], e['t'], e['r']) for e in P.get('ekle', []) if e.get('kat') != 'Kaymakam' and 'doğrulayın' not in e['t']]
            gun = {(e['n'], e['t_old']): e for e in P.get('guncelle', [])}
            L = [(n, gun[(n, t)]['t_new'], r) if (n, t) in gun else (n, t, r) for n, t, r in L]
        except Exception: pass
    out, seen = [], set()
    for n, t, r in sorted(L, key=lambda x: x[2] if isinstance(x[2], (int, float)) else 999):
        if not isinstance(r, (int, float)) or r >= 300 or 'isim girilmemiş' in t: continue
        k = nk(n)
        if k in seen: continue
        seen.add(k); out.append((n, t, r))
    return out

API = 'https://tr.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&redirects=1&prop=pageimages|extracts|description|pageprops&exintro=1&explaintext=1&exsentences=4&piprop=thumbnail|original&pithumbsize=400&ppprop=disambiguation|wikibase_item&titles='
def toplu(basliklar):
    """20 başlığı tek istekte sor (Vikipedi'ye az yük). Hız sınırında bekleyip yeniden dener."""
    for bek in (0, 20, 60, 180):
        if bek: time.sleep(bek)
        raw = get(API + urllib.parse.quote('|'.join(basliklar)), 40)
        if re.search(r'(?i)too many requests|making too many', raw[:400]): continue
        try: q = json.loads(raw)['query']
        except Exception: return None
        yon = {}
        for x in q.get('normalized', []) + q.get('redirects', []): yon[x['from']] = x['to']
        sayfa = {p['title']: p for p in q.get('pages', [])}
        out = {}
        for b in basliklar:
            t = b
            for _ in range(3): t = yon.get(t, t)
            p = sayfa.get(t)
            if not p or p.get('missing'): out[b] = None; continue
            out[b] = {'type': 'disambiguation' if 'disambiguation' in (p.get('pageprops') or {}) else 'standard', 'title': p['title'],
                      'description': p.get('description', ''), 'extract': p.get('extract', ''),
                      'thumbnail': p.get('thumbnail') or {}, 'qid': (p.get('pageprops') or {}).get('wikibase_item', ''), 'url': 'https://tr.wikipedia.org/wiki/' + urllib.parse.quote(p['title'].replace(' ', '_'))}
        return out
    return None

def viki(limit):
    eski = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    bek = []
    for ad, unvan, r in kisiler():
        k = nk(ad)
        if k in DB and (DB[k].get('u') or (DB[k].get('d', '') > eski and not (DB[k].get('neden') == 'sayfada fotoğraf yok' and not DB[k].get('c')))): continue
        bek.append((ad, unvan, re.sub(r'^((Prof|Doç|Dr|Av|Org|Korg|Orgeneral|Korgeneral|Oramiral|Koramiral)\.? )+', '', ad).strip()))
        if len(bek) >= limit: break
    n = 0; red = {}
    for i in range(0, len(bek), 20):
        grup = bek[i:i + 20]
        res = toplu([g[2] for g in grup])
        if res is None: print('Vikipedi hız sınırı / okunamadı; bu tur durduruldu.'); break
        qs = [res[b[2]]['qid'] for b in grup if res.get(b[2]) and res[b[2]].get('qid') and not res[b[2]]['thumbnail']]
        p18 = {}
        if qs:
            try:
                w = json.loads(get('https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids=' + '|'.join(qs), 40))
                for q, e in w.get('entities', {}).items():
                    c = (e.get('claims') or {}).get('P18') or []
                    if c and c[0].get('mainsnak', {}).get('datavalue'):
                        p18[q] = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(c[0]['mainsnak']['datavalue']['value'].replace(' ', '_')) + '?width=400'
            except Exception: pass
        for b in grup:
            j = res.get(b[2])
            if j and not j['thumbnail'] and p18.get(j.get('qid')): j['thumbnail'] = {'source': p18[j['qid']]}; j['commons'] = 1
        for ad, unvan, bas in grup:
            k = nk(ad); j = res.get(bas)
            if j is None: DB[k] = {'n': ad, 'u': '', 'k': '', 'neden': 'Vikipedi sayfası yok', 'd': bugun}; continue
            neden = dogrula(ad, unvan, j)
            img = j['thumbnail'].get('source', '')
            if not neden and not img: neden = 'sayfada fotoğraf yok'
            if neden:
                DB[k] = {'n': ad, 'u': '', 'k': '', 'neden': neden, 'd': bugun, 'c': 1}; red[neden.split(':')[0]] = red.get(neden.split(':')[0], 0) + 1; continue
            DB[k] = {'n': ad, 'u': img, 'k': 'Vikipedi' + (' / Commons' if j.get('commons') else ''), 's': j['url'], 'g': unvan.split(' · ')[0], 'd': bugun}; n += 1
        kaydet(); time.sleep(3)
    print('Vikipedi:', len(bek), 'kişi,', n, 'doğrulanmış fotoğraf; elenen:', red); kaydet()

if __name__ == '__main__':
    a = sys.argv[1:]
    if '--tbmm' in a or not a: tbmm()
    if '--viki' in a: viki(int(a[a.index('--viki') + 1]) if len(a) > a.index('--viki') + 1 else 300)
