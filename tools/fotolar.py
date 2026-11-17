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
# (Türkçe unvan kalıbı, metinde aranacak görev — Türkçe|İngilizce)
ROL = [(r'basbakan', r'basbakan|prime minister'), (r'cumhurbaskani yardimcisi', r'cumhurbaskani yardimcisi|vice president'), (r'cumhurbaskani', r'cumhurbaskan|president|first lady'),
       (r'tbmm baskani|meclis baskani', r'meclis baskan|tbmm baskan|speaker of the grand national'), (r'valisi', r'vali|governor'), (r'bakan yardimcisi', r'bakan yardimcisi|deputy minister'),
       (r'bakani', r'bakan|minister'), (r'rektoru', r'rektor|rector'), (r'buyukelcisi', r'buyukelci|ambassador'),
       (r'orgeneral|oramiral', r'orgeneral|oramiral|komutan|general|admiral|commander'), (r'korgeneral|koramiral', r'korgeneral|koramiral|general|amiral|admiral'),
       (r'tumgeneral|tuggeneral|tumamiral|tugamiral', r'general|amiral|admiral'), (r'komutani', r'komutan|commander'), (r'belediye baskan', r'belediye baskan|mayor'),
       (r'milletvekili', r'milletvekil|member of the grand national assembly|member of parliament|deputy'), (r'yargitay', r'yargitay|court of cassation'), (r'danistay', r'danistay|council of state'),
       (r'anayasa mahkemesi', r'anayasa mahkemesi|constitutional court'), (r'sayistay', r'sayistay|court of accounts'), (r'genel muduru', r'genel mudur|director general|general manager|ceo'),
       (r'baskan yardimcisi|baskanvekili', r'baskan yardimcisi|baskanvekili|vice chair|deputy chair|deputy leader'), (r'kamu denetcisi', r'kamu denetci|ombudsman'), (r'baskani', r'baskan|president|chair|head|leader')]
OLUM = r'(?i)\b(öldü|ölümü|vefat|died|death)|\(\s*(d\.\s*)?\d{1,2}?\s*\w*\s*\d{4}\s*[-–]\s*\d{1,2}?\s*\w*\s*\d{4}\s*\)|ö\.\s*\d{4}'
def dogrula(kisi, unvan, j):
    """Vikipedi özetinin BU kişi ve BUGÜNKÜ (ya da kayıttaki eski) görevi olduğunu doğrula."""
    if j.get('type') != 'standard': return 'anlam ayrımı/özel sayfa'
    tit = nk(j.get('title', ''))
    if tit != nk(kisi) and not (set(nk(kisi).split()) <= set(tit.split())): return 'başlık farklı: ' + j.get('title', '')
    ham = (j.get('description') or '') + ' ' + (j.get('extract') or '')
    metin = norm(ham)
    if re.search(OLUM, ham): return 'ölmüş kişi olabilir'
    # rehberdeki görevlerinden HERHANGİ biri (makam + il/kurum) metinde doğrulanmalı
    son = 'görev doğrulanamadı'
    for parca in unvan.split(' · '):
        if re.search(r'(?i)doğrulayın|dönem$|^\d', parca): continue
        u = norm(re.sub(r'\s*\(.*?\)', '', parca))
        rol = next((r for p, r in ROL if re.search(p, u)), None)
        if not rol or not re.search(rol, metin): continue
        ayirt = [w for w in u.split() if w not in GENEL and len(w) > 2 and not re.search(rol, w)]
        if ayirt and not any(w[:6] in metin for w in ayirt): son = 'il/kurum doğrulanamadı'; continue
        return ''
    return son

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

PROP = 'action=query&format=json&formatversion=2&redirects=1&prop=pageimages|extracts|description|pageprops&exintro=1&explaintext=1&exsentences=8&piprop=thumbnail|original&pithumbsize=400&ppprop=disambiguation|wikibase_item'
def sor(lang, ek):
    """Vikipedi API; hız sınırında bekleyip yeniden dener."""
    for bek in (0, 20, 60, 180):
        if bek: time.sleep(bek)
        raw = get('https://%s.wikipedia.org/w/api.php?%s&%s' % (lang, PROP, ek), 40)
        if re.search(r'(?i)too many requests|making too many', raw[:400]): continue
        try: return json.loads(raw).get('query', {})
        except Exception: return None
    return None
def sayfa_kaydi(lang, p):
    return {'type': 'disambiguation' if 'disambiguation' in (p.get('pageprops') or {}) else 'standard', 'title': p['title'],
            'description': p.get('description', ''), 'extract': p.get('extract', ''), 'thumbnail': p.get('thumbnail') or {},
            'qid': (p.get('pageprops') or {}).get('wikibase_item', ''), 'lang': lang,
            'url': 'https://%s.wikipedia.org/wiki/%s' % (lang, urllib.parse.quote(p['title'].replace(' ', '_')))}
def toplu(basliklar, lang='tr'):
    """20 başlığı tek istekte sor (Vikipedi'ye az yük)."""
    q = sor(lang, 'titles=' + urllib.parse.quote('|'.join(basliklar)))
    if q is None: return None
    yon = {}
    for x in q.get('normalized', []) + q.get('redirects', []): yon[x['from']] = x['to']
    sayfa = {p['title']: p for p in q.get('pages', [])}
    out = {}
    for b in basliklar:
        t = b
        for _ in range(3): t = yon.get(t, t)
        p = sayfa.get(t)
        out[b] = None if not p or p.get('missing') else sayfa_kaydi(lang, p)
    return out
def ara(lang, ad):
    """Başlığı farklı yazılmış sayfalar için ("Ali Veli (siyasetçi)" gibi) isimle arama; ilk 5 aday."""
    q = sor(lang, 'generator=search&gsrlimit=5&gsrnamespace=0&gsrsearch=' + urllib.parse.quote('"' + ad + '"'))
    if q is None: return None
    return [sayfa_kaydi(lang, p) for p in sorted(q.get('pages', []), key=lambda p: p.get('index', 99)) if not p.get('missing')]
def commons(kayitlar):
    """Doğrulanmış sayfanın Vikidata kaydındaki resmî görsel (P18) — sayfa özetinde resim yoksa."""
    qs = [j['qid'] for j in kayitlar if j and j.get('qid') and not j['thumbnail']]
    if not qs: return
    try:
        w = json.loads(get('https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids=' + '|'.join(qs[:50]), 40))
        for j in kayitlar:
            e = w.get('entities', {}).get(j.get('qid', '') if j else '', {})
            c = (e.get('claims') or {}).get('P18') or []
            if j and not j['thumbnail'] and c and c[0].get('mainsnak', {}).get('datavalue'):
                j['thumbnail'] = {'source': 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(c[0]['mainsnak']['datavalue']['value'].replace(' ', '_')) + '?width=400'}; j['commons'] = 1
    except Exception: pass
SURUM = 4  # arama yöntemi değişince eski "bulunamadı" kayıtları bir kez yeniden denenir
def sonuc(ad, unvan, j):
    neden = dogrula(ad, unvan, j)
    if not neden and not j['thumbnail'].get('source'): neden = 'sayfada fotoğraf yok'
    return neden
def kabul(ad, unvan, j):
    DB[nk(ad)] = {'n': ad, 'u': j['thumbnail']['source'], 'k': 'Vikipedi' + (' (EN)' if j['lang'] == 'en' else '') + (' / Commons' if j.get('commons') else ''),
                  's': j['url'], 'g': unvan.split(' · ')[0], 'd': bugun}

def viki(limit):
    eski = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    bek = []
    for ad, unvan, r in kisiler():
        k = nk(ad)
        if k in DB and (DB[k].get('u') or (DB[k].get('d', '') > eski and DB[k].get('v') == SURUM)): continue
        bek.append((ad, unvan, re.sub(r'^((Prof|Doç|Dr|Av|Org|Korg|Orgeneral|Korgeneral|Oramiral|Koramiral|Tümgeneral|Tuğgeneral)\.? )+', '', ad).strip()))
        if len(bek) >= limit: break
    n = 0; red = {}; dur = False
    for i in range(0, len(bek), 20):
        grup = bek[i:i + 20]
        # 1) Türkçe Vikipedi, tam başlık (toplu)  2) İngilizce Vikipedi, tam başlık (toplu)
        kalan = list(grup); neden = {}
        for lang in ('tr', 'en'):
            if not kalan: break
            res = toplu([g[2] for g in kalan], lang)
            if res is None: dur = True; break
            commons(list(res.values()))
            yeni = []
            for g in kalan:
                j = res.get(g[2])
                nd = sonuc(g[0], g[1], j) if j else 'Vikipedi sayfası yok'
                if not nd: kabul(g[0], g[1], j); n += 1
                else: neden[g[0]] = neden.get(g[0]) if lang == 'en' and neden.get(g[0]) != 'Vikipedi sayfası yok' else nd; yeni.append(g)
            kalan = yeni; time.sleep(2)
        # 3) isimle arama (başlığı farklı yazılmış sayfalar), önce Türkçe sonra İngilizce
        for g in kalan:
            if dur: break
            for lang in ('tr', 'en'):
                c = ara(lang, g[2])
                if c is None: dur = True; break
                c = [j for j in c if set(nk(g[2]).split()) <= set(nk(j['title']).split())]
                commons(c)
                ok = next((j for j in c if not sonuc(g[0], g[1], j)), None)
                time.sleep(1)
                if ok: kabul(g[0], g[1], ok); n += 1; break
            else:
                k = nk(g[0]); nd = neden.get(g[0], 'bulunamadı')
                DB[k] = {'n': g[0], 'u': '', 'k': '', 'neden': nd, 'd': bugun, 'v': SURUM}; red[nd.split(':')[0]] = red.get(nd.split(':')[0], 0) + 1
        kaydet()
        if dur: print('Vikipedi hız sınırı; bu tur durduruldu.'); break
    print('Vikipedi:', len(bek), 'kişi,', n, 'doğrulanmış fotoğraf; elenen:', red); kaydet()

ILLER = 'adana adiyaman afyonkarahisar agri aksaray amasya ankara antalya ardahan artvin aydin balikesir bartin batman bayburt bilecik bingol bitlis bolu burdur bursa canakkale cankiri corum denizli diyarbakir duzce edirne elazig erzincan erzurum eskisehir gaziantep giresun gumushane hakkari hatay igdir isparta istanbul izmir kahramanmaras karabuk karaman kars kastamonu kayseri kilis kirikkale kirklareli kirsehir kocaeli konya kutahya malatya manisa mardin mersin mugla mus nevsehir nigde ordu osmaniye rize sakarya samsun sanliurfa siirt sinop sirnak sivas tekirdag tokat trabzon tunceli usak van yalova yozgat zonguldak'.split()
def resmi_site(ad, unvan, adresler, kelime, kaynak):
    """Resmî kurum sitesinde kişinin adı geçiyorsa, adıyla ya da makam kelimesiyle eşleşen resmi al."""
    k = nk(ad)
    for u in adresler:
        h = get(u, 15)
        if not h or k not in nk(re.sub(r'<[^>]+>', ' ', html.unescape(h))): continue
        aday = []
        for im in re.finditer(r'<img\b[^>]*>', h, re.I):
            t = im.group(0); src = re.search(r'\b(?:data-src|src)=["\']([^"\']+)', t)
            if not src or re.search(r'(?i)logo|icon|bayrak|flag|\.svg|banner|ataturk|cumhurbaskani|erdogan', src.group(1)): continue
            yol = norm(urllib.parse.unquote(html.unescape(src.group(1))))
            # haber / etkinlik / galeri görselleri ASLA (kalabalık fotoğraf, yanlış kişi riski)
            if re.search(r'haber|gundem|whatsapp|duyuru|etkinlik|ziyaret|slider|galeri|toplanti|tören|toren|bayram|cumhurbaskan|bakan|img \d|dsc|\d{6,}', yol): continue
            alt = norm(' '.join(re.findall(r'\b(?:alt|title)=["\']([^"\']*)', t)))
            soyad = nk(ad).split()[-1]
            puan = (5 if soyad in yol.replace(' ', '') or soyad in yol else 0) + (4 if re.search(r'yoneticilerimiz|' + kelime + r'imiz|ozgecmis|biyografi', yol) else 0) + (2 if k in nk(alt) else 0)
            if puan >= 4: aday.append((puan, urllib.parse.urljoin(u, html.unescape(src.group(1)))))
        if aday:
            aday.sort(key=lambda x: -x[0])
            if k not in DB or not DB[k].get('u') or DB[k].get('k') == kaynak:
                DB[k] = {'n': ad, 'u': aday[0][1], 'k': kaynak, 's': u, 'g': unvan.split(' · ')[0], 'd': bugun}; return True
            return False
        time.sleep(0.4)
    return False
def yeni_mi(k, kaynak):
    return not (k in DB and (DB[k].get('u') or DB[k].get('k') == kaynak) and DB[k].get('d', '') > (datetime.date.today() - datetime.timedelta(days=30)).isoformat())
def valilik():
    """Valiler: il valiliğinin resmî sitesi (www.<il>.gov.tr)."""
    n = kontrol = 0
    for ad, unvan, r in kisiler():
        m = re.match(r'(.+?) Valisi$', unvan.split(' · ')[0].strip())
        if not m: continue
        il = norm(m.group(1)).replace(' ', '')
        if il not in ILLER or not yeni_mi(nk(ad), 'Valilik'): continue
        kontrol += 1
        if resmi_site(ad, unvan, ['https://www.%s.gov.tr%s' % (il, y) for y in ('/vali', '/valimiz', '')], 'vali', 'Valilik'): n += 1
        time.sleep(0.4)
    print('Valilik:', kontrol, 'vali denendi,', n, 'resmî fotoğraf'); kaydet()
def kaymakamlik(limit):
    """Kaymakamlar: kaymakamlığın resmî sitesi (www.<ilçe>.gov.tr). Günde 'limit' kişi, 30 günde bir yenilenir."""
    try: P = json.load(open(os.path.join(R, 'data', 'rehber.json'), encoding='utf-8'))
    except Exception: return
    n = kontrol = 0
    for e in P.get('ekle', []):
        if e.get('kat') != 'Kaymakam' or 'doğrulayın' in e['t']: continue
        m = re.match(r'(.+?) Kaymakamı \((.+?)\)', e['t'])
        if not m or not yeni_mi(nk(e['n']), 'Kaymakamlık'): continue
        if kontrol >= limit: break
        ilce, il = norm(m.group(1)).replace(' ', ''), norm(m.group(2)).replace(' ', '')
        kontrol += 1
        adr = ['https://www.%s.gov.tr%s' % (d, y) for d in (ilce, il + ilce) for y in ('/kaymakam', '/kaymakamimiz', '')]
        if resmi_site(e['n'], e['t'], adr, 'kaymakam', 'Kaymakamlık'): n += 1
        else: DB.setdefault(nk(e['n']), {'n': e['n'], 'u': '', 'k': '', 'neden': 'kaymakamlık sitesinde bulunamadı', 'd': bugun})['d'] = bugun
        if kontrol % 25 == 0: kaydet()
        time.sleep(0.4)
    print('Kaymakamlık:', kontrol, 'kaymakam denendi,', n, 'resmî fotoğraf'); kaydet()

KURUM_SAYFA = {'THY': ['https://investor.turkishairlines.com/tr/kurumsal-yonetim/yonetim-kurulu', 'https://investor.turkishairlines.com/tr/kurumsal-yonetim/ust-yonetim'],
               # TGS sitesi (tgs.aero) yönetim kadrosu yayımlamıyor: /kurumsal/* ana sayfaya yönleniyor (17.11.2026 keşif)
               }
def kurum_yonetim():
    """THY / TGS yöneticileri: şirketin resmî yönetim sayfası. Resim etiketinden hemen sonra gelen ad, rehberdeki aynı kurumun kişisiyle eşleşmeli."""
    src = open(os.path.join(R, 'index.html'), encoding='utf-8').read(); i = src.index('K0=')
    K = json.JSONDecoder().raw_decode(src[i + 3:])[0]
    rehber = {}
    for x in K:
        if x[5] in KURUM_SAYFA: rehber.setdefault((x[5], nk(x[0])), x)
    n = 0; yeni = []
    for kurum, sayfalar in KURUM_SAYFA.items():
        for u in sayfalar:
            h = get(u, 40)
            if not h: continue
            parca = re.split(r'(<img\b[^>]*>)', h, flags=re.I)
            for ix in range(1, len(parca), 2):
                t = parca[ix]; s_ = re.search(r'\bsrc=["\']([^"\']+)', t)
                if not s_ or re.search(r'(?i)logo|icon|\.svg|footer|award|odul', s_.group(1)): continue
                alt = html.unescape(' '.join(re.findall(r'\balt=["\']([^"\']*)', t))).strip()
                sonra = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', ''.join(parca[ix + 1:ix + 2]))))[:300].strip()
                # ad = resimden sonraki metnin unvandan (alt) önceki kısmı
                kes = sonra.find(alt.split('/')[0].strip()[:20]) if alt else -1
                ad = (sonra[:kes] if kes > 0 else ' '.join(sonra.split()[:4])).strip(' -–·|')
                if not ad or len(ad) > 60: continue
                k = nk(ad); x = rehber.get((kurum, k)) or next((v for (kk, kn), v in rehber.items() if kk == kurum and (kn.endswith(' ' + k) or k.endswith(' ' + kn))), None)
                if not x: yeni.append(kurum + ': ' + ad + ' — ' + alt); continue
                DB[nk(x[0])] = {'n': x[0], 'u': urllib.parse.urljoin(u, html.unescape(s_.group(1))), 'k': kurum + ' resmî sitesi', 's': u, 'g': alt or x[1], 'd': bugun}; n += 1
            time.sleep(1)
    print('Kurum yönetimi:', n, 'resmî fotoğraf eşleşti')
    if yeni: print('Rehberde olmayan (yönetici onayı için):', *yeni, sep='\n  ')
    kaydet()

if __name__ == '__main__':
    a = sys.argv[1:]
    sayi = lambda k, v: int(a[a.index(k) + 1]) if len(a) > a.index(k) + 1 and a[a.index(k) + 1].isdigit() else v
    if not a: tbmm()
    for k in a:  # komut satırındaki sırayla
        if k == '--tbmm': tbmm()
        elif k == '--kurum': kurum_yonetim()
        elif k == '--vali': valilik()
        elif k == '--viki': viki(sayi('--viki', 300))
        elif k == '--kaymakam': kaymakamlik(sayi('--kaymakam', 150))
