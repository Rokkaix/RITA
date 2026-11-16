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

def pdf_text(b):
    try:
        from pypdf import PdfReader
        return '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages)
    except Exception as e:
        print('PDF okunamadı:', e); return ''

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

def gun(d):
    """Bir günün gazetesindeki atama kararı belgeleri -> kayıtlar."""
    y, mo = d[:4], d[4:6]
    idx = get(f'{BASE}eskiler/{y}/{mo}/{d}.htm')
    if 'ATAMA' not in idx.upper(): return []
    sec = idx.upper().find('ATAMA KARAR'); part = idx[sec:sec + 20000] if sec >= 0 else idx
    links = []
    for m in re.finditer(r'href="([^"]+?(?:\.pdf|\.htm))"', part, re.I):
        u = m.group(1)
        if d in u and u not in links: links.append(u)
        if re.search(r'</ul>|<h\d', part[m.end():m.end() + 300] or ''): pass
    kayit = []
    for u in links[:15]:
        full = u if u.startswith('http') else BASE + u.lstrip('./')
        if not re.search(rf'{d}-\d+', full): continue
        body = pdf_text(get(full, True)) if full.lower().endswith('.pdf') else html.unescape(re.sub(r'<[^>]+>', ' ', get(full)))
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
    days = args or [(today - datetime.timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]
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
            C[did] = {'tarih': f'{d[:4]}-{d[4:6]}-{d[6:]}', 'tur': tur, 'makam': makam, 'eski': eski, 'yeni': ynn,
                      'sebep': 'Resmî Gazete atama kararı' + (f' ({kno})' if kno else ''), 'kaynak': f'Resmî Gazete {d[6:]}.{d[4:6]}.{d[:4]} · {url}',
                      'durum': 'beklemede', 'ekleyen': 'resmi-gazete', 'r': 0}
            yeni += 1
    if yeni:
        V['guncelleme'] = datetime.datetime.now(TR).isoformat(timespec='seconds')
        json.dump(V, open(VERI, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Yeni kayıt:', yeni)

if __name__ == '__main__':
    main()
