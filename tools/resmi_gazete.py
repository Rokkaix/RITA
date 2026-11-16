"""Resmî Gazete atama / görevden alma kararlarını okur, rical ile ilgili olanları
data/rita-veri.json → degisiklikler içine "beklemede" kayıt olarak ekler (yönetici onaylar).
GitHub Actions'ta düzenli çalışır. Son 3 günün gazetesine bakar; aynı kayıt iki kez eklenmez.
Kullanım: python3 tools/resmi_gazete.py [YYYYMMDD ...]   |   test: python3 tools/resmi_gazete.py --metin dosya.txt"""
import json, os, re, sys, subprocess, datetime, hashlib, html, io
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(R, 'data', 'rita-veri.json')
BASE = 'https://www.resmigazete.gov.tr/'
TR = datetime.timezone(datetime.timedelta(hours=3))

def get(url, binary=False):
    r = subprocess.run(['curl', '-sL', '-m', '60', '-A', 'Mozilla/5.0', url], capture_output=True)
    return r.stdout if binary else r.stdout.decode('utf-8', 'ignore')

def ocr_pdf(b):
    """Atama kararları PDF'te resim olarak durur: sayfaları resme çevirip Türkçe OCR ile okur (pdftoppm + tesseract)."""
    import tempfile, glob, shutil
    if not shutil.which('pdftoppm') or not shutil.which('tesseract'):
        print('OCR araçları yok (pdftoppm/tesseract)'); return ''
    d = tempfile.mkdtemp(); f = os.path.join(d, 'k.pdf'); open(f, 'wb').write(b)
    subprocess.run(['pdftoppm', '-r', '300', '-gray', '-png', f, os.path.join(d, 's')], capture_output=True)
    out = []
    for img in sorted(glob.glob(os.path.join(d, 's*.png'))):
        r = subprocess.run(['tesseract', img, '-', '-l', 'tur', '--psm', '6'], capture_output=True, text=True)
        out.append(r.stdout)
    shutil.rmtree(d, ignore_errors=True)
    return '\n'.join(out)

def pdf_text(b):
    t = ''
    try:
        from pypdf import PdfReader
        t = '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages)
    except Exception as e:
        print('PDF metni okunamadı:', e)
    if 'atan' not in t and 'görevden' not in t and len(b) > 1000:
        o = ocr_pdf(b)
        if o:
            print('   (OCR ile okundu)')
            if os.environ.get('RG_KURU'): print('      OCR:', re.sub(r'\s+', ' ', o)[:2500])
            t = t + '\n' + o
    return t

UP = r"[A-ZÇĞİÖŞÜÂÎÛ]"
GW = rf"(?!\S*(?:ğına|ğine|ğuna|ğüne)\b)(?!(?:Müdürü|Başkanı|Valisi|Rektörü|Büyükelçisi|Sekreteri|Yardımcısı|Üyesi|Komutanı|Başsavcısı|Başkanvekili|Temsilcisi|Müsteşarı)\b){UP}[a-zçğıöşüâîû]+\.?"
NAME = rf"((?:{GW} ){{1,3}}(?:{UP}{{2,}}[\-’']?)(?: {UP}{{2,}})?)"
# makam ekini sadeleştir: "Genel Müdürlüğüne" -> "Genel Müdürü"
EK = [(r'Bakan Yardımcılığına$', 'Bakan Yardımcısı'), (r'Genel Müdürlüğüne$', 'Genel Müdürü'), (r'Başkanlığına$', 'Başkanı'),
      (r'Valiliğine$', 'Valisi'), (r'Rektörlüğüne$', 'Rektörü'), (r'Büyükelçiliğine$', 'Büyükelçisi'), (r'Genel Sekreterliğine$', 'Genel Sekreteri'),
      (r'Üyeliğine$', 'Üyesi'), (r'Başsavcılığına$', 'Başsavcısı'), (r'Komutanlığına$', 'Komutanı'), (r'Müsteşarlığına$', 'Müsteşarı'),
      (r'Daimi Temsilciliğine$', 'Daimi Temsilcisi'), (r'Başkan Vekilliğine$', 'Başkanvekili'), (r'Başkanvekilliğine$', 'Başkanvekili')]
ALAKA = re.compile(r'Bakan Yardımcısı|Genel Müdürü|Başkanı|Valisi|Rektörü|Büyükelçisi|Genel Sekreteri|Başsavcısı|Komutanı|Müsteşarı|Daimi Temsilcisi|Başkanvekili|Kurulu Üyesi|Kurul Üyesi')
DISLA = re.compile(r'Daire Başkan|Bölge Müdür|İl Müdür|İlçe|Müftü|Hastane|Genel Müdür Yardımc|Başkan Yardımc|Şube|Kaymakam|Dekan|Müdür Yardımc|Başhekim|Grup Başkan')

def sade(m):
    m = re.sub(r'\s+', ' ', m).strip(' ,;:-')
    m = re.sub(r'^(?:\d+[\-–.)]\s*)', '', m)
    m = re.sub(r'^.*Karar Sayısı\s*:\s*\S+\s*', '', m)
    m = re.sub(r'^.*?(?:ATAMA KARARLARI|Atama Kararı|Cumhurbaşkanı Kararı)\s*', '', m)
    m = re.sub(r'(\S+) Bakanlığında (?:boş|açık) bulunan Bakan Yardımcılığına', r'\1 Bakan Yardımcılığına', m)
    m = re.sub(r'(?:’|\')?(?:n|d|t)?(?:a|e)\s+(?:boş|açık) bulunan\s+', ' ', m)
    m = re.sub(r'\b(?:boş|açık) bulunan\s+', '', m)
    for a, b in EK:
        if re.search(a, m): return re.sub(a, b, m)
    return m

def tc(n):
    return ' '.join(w if not (w.isupper() and len(w) > 1) else w[0] + w[1:].replace('I', 'ı').replace('İ', 'i').lower() for w in n.split())

def ayikla(txt):
    """Metinden (tur, makam, eski, yeni) kayıtları."""
    t = re.sub(r'-\n', '', txt); t = re.sub(r'\s+', ' ', t)
    out = []
    for s in re.split(r'(?<=(?:mıştır|miştir|muştur|müştür)\.)\s*', t):
        s = s.strip()
        if not s: continue
        m = re.search(rf'^(.*?) {NAME} görevden alın(?:mış|arak)[, ]+yerine {NAME} atanmıştır\.$', s)
        if m: out.append(('atama', sade(m.group(1)), tc(m.group(2)), tc(m.group(3)))); continue
        m = re.search(rf'^(.*?) {NAME} (?:görevden alınmıştır|görevinden alınmıştır)\.$', s)
        if m: out.append(('gorevden_alma', sade(m.group(1)), tc(m.group(2)), '')); continue
        m = re.search(rf'^(.*?) {NAME} (?:atanmıştır|görevlendirilmiştir)\.$', s)
        if m: out.append(('atama', sade(m.group(1)), '', tc(m.group(2)))); continue
    return [o for o in out if ALAKA.search(o[1]) and not DISLA.search(o[1]) and len(o[1]) < 160]

# ---- teyit: makam RITA'nın bildiği bir makamla eşleşmeli, isimler düzgün olmalı ----
def _norm(t):
    import unicodedata
    t = (t or '').replace('İ', 'i').replace('I', 'ı').lower().translate(str.maketrans('şğüöçı', 'sguoci'))
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', t)).strip()
_BIL = None
def bilinen():
    """RITA'daki makamlar: rehber unvanları, kurum listesi, valilikler, üniversiteler, bakanlıklar."""
    global _BIL
    if _BIL is not None: return _BIL
    src = open(os.path.join(R, 'index.html'), encoding='utf-8').read()
    def arr(name):
        i = src.index(name + '='); return json.JSONDecoder().raw_decode(src[i + len(name) + 1:])[0]
    M = {}
    add = lambda t: M.setdefault(_norm(t), t)
    for x in arr('K0'):
        for q in str(x[1]).split(' · '):
            q = re.sub(r'\s*\(.*?\)', '', q)
            if not re.match(r'(?i)eski|emekli', q) and len(q) > 6:
                add(q)
                if '(' in str(x[1]): pass
    G = arr('GMC')
    for r in G['rows']: add(r['u'])
    bak = {_norm(r['b']) for r in G['rows'] if 'Bakanlığı' in r['b']}
    K = os.path.join(R, 'data', 'rehber-kaynak')
    try:
        for v in json.load(open(os.path.join(K, 'valiler.json'), encoding='utf-8')): add(v['il'] + ' Valisi')
        for u in json.load(open(os.path.join(K, 'rektorler.json'), encoding='utf-8')): add(u['uni'] + ' Rektörü')
    except Exception: pass
    for r in G['rows']:
        if 'Bakanlığı' in r['b']: add(r['b'].replace('Bakanlığı', 'Bakan Yardımcısı'))
    ABBR = {'Bankacılık Düzenleme ve Denetleme Kurumu': 'BDDK', 'Sermaye Piyasası Kurulu': 'SPK', 'Enerji Piyasası Düzenleme Kurumu': 'EPDK',
            'Bilgi Teknolojileri ve İletişim Kurumu': 'BTK', 'Kamu İhale Kurumu': 'KİK', 'Radyo ve Televizyon Üst Kurulu': 'RTÜK',
            'Kişisel Verileri Koruma Kurumu': 'KVKK', 'Tasarruf Mevduatı Sigorta Fonu': 'TMSF', 'Kamu Gözetimi, Muhasebe ve Denetim Standartları Kurumu': 'KGK',
            'Sosyal Güvenlik Kurumu': 'SGK', 'Türkiye İstatistik Kurumu': 'TÜİK', 'Türkiye Cumhuriyet Merkez Bankası': 'TCMB', 'Devlet Hava Meydanları İşletmesi': 'DHMİ'}
    for uzun, kisa in ABBR.items():
        for suf in (' Başkanı', ' Genel Müdürü'):
            if _norm(kisa + suf) in M: M[_norm(uzun + suf)] = M[_norm(kisa + suf)]
    M.pop('', None)
    _BIL = M
    return _BIL
GENEL = set('genel muduru mudur baskani baskan sekreteri yardimcisi bakan rektoru valisi buyukelcisi uyesi kurulu kurumu baskanvekili komutani bassavcisi mustesari ve daimi temsilcisi'.split())
def teyit(makam, eski, yeni):
    """(durum, kanonik_makam, açıklama). Yalnızca kesin eşleşme 'otomatik' olur."""
    ad = re.compile(r"^[A-ZÇĞİÖŞÜÂÎÛ][a-zçğıöşüâîû]+(?: [A-ZÇĞİÖŞÜÂÎÛ][a-zçğıöşüâîû'’\-]+){1,4}$")
    for n in (eski, yeni):
        if n and not ad.match(n): return 'beklemede', makam, 'isim okunamadı: ' + n
    nm = _norm(makam)
    if re.search(r'buyukelcisi$', nm) and re.search(r'nezdinde|buyukelciligine|buyukelcisi', nm):
        return 'otomatik', makam, 'Resmî Gazete metni; büyükelçi ataması'
    B = bilinen()
    for k in sorted(B, key=len, reverse=True):
        if len(k) >= 10 and set(k.split()) - GENEL and (nm == k or nm.endswith(' ' + k) or (len(set(nm.split()) - GENEL) >= 1 and k.endswith(' ' + nm))):
            return 'otomatik', B[k], 'Resmî Gazete metni; makam RITA kayıtlarıyla eşleşti'
    return 'beklemede', makam, 'makam RITA kayıtlarında bulunamadı; elle kontrol edilmeli'

def gun(d):
    """Bir günün gazetesindeki atama kararı belgeleri -> kayıtlar."""
    y, mo = d[:4], d[4:6]
    IU = f'{BASE}eskiler/{y}/{mo}/{d}.htm'
    idx = get(IU)
    print(f'  {d}: fihrist {len(idx)} bayt, ATAMA geçiyor: {"ATAMA" in idx.upper()}')
    if 'ATAMA' not in idx.upper(): return []
    sec = idx.upper().find('ATAMA KARAR'); part = idx[sec:sec + 20000] if sec >= 0 else idx
    if os.environ.get('RG_KURU'): print('  FİHRİST:', re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', idx[max(0, sec - 200):sec + 1500])))
    links = []
    for m in re.finditer(r'href="([^"]+?(?:\.pdf|\.htm))"', part, re.I):
        u = m.group(1)
        if d in u and 'ilanlar' not in u and u not in links: links.append(u)
        if re.search(r'</ul>|<h\d', part[m.end():m.end() + 300] or ''): pass
    print(f'  {d}: {len(links)} bağlantı', links[:6])
    kayit = []
    for u in links[:15]:
        import urllib.parse
        full = urllib.parse.urljoin(IU, u)
        if not re.search(rf'{d}-\d+', full): continue
        body = pdf_text(get(full, True)) if full.lower().endswith('.pdf') else html.unescape(re.sub(r'<[^>]+>', ' ', get(full)))
        print(f'   {full}: {len(body)} karakter')
        if os.environ.get('RG_KURU'): print('      ÖRNEK:', re.sub(r'\s+', ' ', body)[:700])
        if 'atan' not in body and 'görevden' not in body: continue
        ks = re.search(r'Karar Sayısı\s*:\s*([0-9/]+)', body)
        for k in ayikla(body):
            kayit.append(k + (full, ks.group(1) if ks else ''))
    return kayit

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--metin' in sys.argv:
        for k in ayikla(open(args[0], encoding='utf-8').read()): print(k)
        return
    today = datetime.datetime.now(TR).date()
    env = os.environ.get('RG_GUNLER', '').split()
    days = args or env or [(today - datetime.timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]
    V = json.load(open(VERI, encoding='utf-8')); C = V.setdefault('degisiklikler', {})
    var = {(re.sub(r'\W', '', (c.get('makam') or '').lower()), (c.get('yeni') or c.get('eski') or '').lower()) for c in C.values()}
    yeni = 0
    for d in days:
        try: ks = gun(d)
        except Exception as e: print('Okunamadı', d, e); continue
        print(d, len(ks), 'kayıt')
        for tur, makam, eski, ynn, url, kno in ks:
            key = (re.sub(r'\W', '', makam.lower()), (ynn or eski).lower())
            if key in var: continue
            var.add(key)
            did = 'rg-' + d + '-' + hashlib.sha1((makam + eski + ynn).encode()).hexdigest()[:8]
            durum, makam2, aciklama = teyit(makam, eski, ynn)
            C[did] = {'rg_metin': makam, 'tarih': f'{d[:4]}-{d[4:6]}-{d[6:]}', 'tur': tur, 'makam': makam2, 'eski': eski, 'yeni': ynn,
                      'sebep': 'Resmî Gazete atama kararı' + (f' ({kno})' if kno else ''), 'kaynak': f'Resmî Gazete {d[6:]}.{d[4:6]}.{d[:4]} · {url}',
                      'durum': durum, 'teyit': aciklama, 'ekleyen': 'resmi-gazete', 'eklendi': datetime.datetime.now(TR).isoformat(timespec='seconds'), 'r': 0}
            yeni += 1
    if os.environ.get('RG_KURU'):
        for k, v in C.items():
            if v.get('ekleyen') == 'resmi-gazete' and k.startswith('rg-'): pass
        print('Kuru deneme: dosyaya yazılmadı. Bulunanlar:'); [print('  ', v['tarih'], v['durum'], v['makam'], '|', v['eski'], '->', v['yeni'], '|', v.get('teyit')) for k, v in C.items() if v.get('ekleyen') == 'resmi-gazete']
        return
    if yeni:
        V['guncelleme'] = datetime.datetime.now(TR).isoformat(timespec='seconds')
        json.dump(V, open(VERI, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Yeni kayıt:', yeni)

if __name__ == '__main__':
    main()
