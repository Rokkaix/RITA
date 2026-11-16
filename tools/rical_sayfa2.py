"""Tek seferlik geçiş (16.11.2026): Başkent Protokol Listesi 2. sayfa (49–82) rical listesine eklendi.
Eski sıra numaraları (50–209) yeni listeye taşınır. Kullanım: python3 tools/rical_sayfa2.py  (index.html'i günceller)"""
import json, re, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'index.html')
src = open(P, encoding='utf-8').read()
lines = src.split('\n'); LN = next(i for i, l in enumerate(lines) if l.startswith('const RS=['))
L = lines[LN]
def span(name):
    i = L.index(name + '=') + len(name) + 1; v, e = json.JSONDecoder().raw_decode(L[i:]); return i, i + e, v
OLD = span('RS')[2]
if len(OLD) != 209:   # geçiş yapılmış: eski liste kayıtlı kopyadan
    OLD = json.load(open(os.path.join(R, 'tools', 'rical_eski_liste.json'), encoding='utf-8'))
    if __name__ == '__main__': sys.exit('liste zaten yeni; geçiş bir kez yapılır')
assert len(OLD) == 209 and OLD[49].startswith('Yargıtay, Danıştay')
B = lambda k: ('B', k)      # Başkent 2. sayfa maddesi
O = lambda k: ('O', k)      # eski (THY) madde
P2 = {49: 'Rekabet Kurumu Başkanı', 50: 'Özelleştirme İdaresi Başkanı', 51: 'Sermaye Piyasası Kurulu Başkanı', 52: 'Diyanet İşleri Başkanı',
      53: 'Cumhurbaşkanlığı Genel Sekreter Yardımcıları', 54: 'TBMM Genel Sekreter Yardımcıları', 55: 'Tümgeneraller / Tümamiraller',
      56: 'Başbakanlık ve Bakanlıklar Müsteşar Yardımcıları', 57: 'Yargıtay Daire Başkanları ve Üyeleri', 58: 'Danıştay Daire Başkanları ve Üyeleri',
      59: 'Sayıştay Daire Başkanları ve Üyeleri', 60: 'Devlet Personel Başkanı', 61: 'Türkiye Atom Enerjisi Kurumu Başkanı', 62: 'TÜBİTAK Başkanı',
      63: 'Ankara’daki Üniversitelerin Rektör Yardımcıları', 64: 'Yüksek Seçim Kurulu Üyeleri', 65: 'Merkezde Görevli Türk Büyükelçileri',
      66: 'Merkezde Görevli Valiler', 67: 'Devlet Denetleme Kurulu Üyeleri', 68: 'Kamu Denetçiliği Kurumu Denetçileri', 69: 'Tuğgeneraller / Tuğamiraller',
      70: 'YÖK Genel Sekreteri', 71: 'Türkiye İstatistik Kurumu Başkanı', 72: 'Basın Yayın ve Enformasyon Genel Müdürü', 73: 'Anadolu Ajansı Genel Müdürü',
      74: 'TRT Genel Müdürü', 75: 'Devlet Meteoroloji İşleri Genel Müdürü', 76: 'Vakıflar Genel Müdürü', 77: 'Tapu ve Kadastro Genel Müdürü',
      78: 'Türkiye ve Orta Doğu Amme İdaresi Enstitüsü Genel Müdürü', 79: 'Başbakanlık ve Bakanlıklar Genel Müdürleri',
      80: 'Ankara’daki Fakültelerin Dekanları, Yardımcıları', 81: 'Ankara’daki Kamu Kurumu Niteliğindeki Meslek Kuruluşları Başkanları', 82: 'Sivil ve Askerî Dernek Başkanları'}
ORDER = [B(49), B(50), B(51), O(53), B(52), B(53), B(54), B(55), O(54), O(55), B(56), B(57), B(58), B(59), B(60), B(61), B(62), B(63), B(64), B(65),
         O(58), O(59), B(66), O(60), O(61), B(67), O(63), O(64), O(65), O(66), O(68), B(68), B(69), B(70), B(71), B(72), B(73), B(74), B(75), B(76),
         B(77), B(78), B(79), O(73), B(80), B(81), B(82)] + [O(k) for k in range(76, 210) if k != 138]
NEW = OLD[:49] + [P2[x[1]] if x[0] == 'B' else (OLD[x[1] - 1] if x[1] != 53 else 'BTK, BDDK, EPDK, KİK, TAPDK, Şeker Kurumu başkanları ve benzeri düzenleyici kurul başkanları') for x in ORDER]
assert sorted(k for t, k in ORDER if t == 'B') == list(range(49, 83))
pos = {x: i + 50 for i, x in enumerate(ORDER)}
M = {k: pos[O(k)] for k in range(50, 210) if O(k) in pos}
M.update({52: pos[B(52)], 56: pos[B(56)], 62: pos[B(67)], 67: pos[B(50)], 69: pos[B(60)], 70: pos[B(71)], 71: pos[B(79)], 72: pos[B(71)],
          74: pos[B(62)], 75: pos[B(61)], 138: pos[B(68)]})
def n(t): return (t or '').replace('İ', 'i').replace('I', 'ı').lower()
def m(r, t=''):
    if not isinstance(r, (int, float)) or r <= 0 or r >= 300: return r
    b = int(r); f = round(r - b, 4)
    if b < 50: return r
    t = n(t)
    if b == 50: return pos[B(58)] if 'danıştay' in t else pos[B(59)] if 'sayıştay' in t else pos[B(57)]
    if b == 51: return pos[B(69)] if (abs(f - 0.2) < .05 or re.search(r'tuğ(general|amiral)', t)) else pos[B(55)]
    if b == 53: return pos[B(49)] if 'rekabet' in t else pos[B(51)] if re.search(r'sermaye piyasası|\bspk\b', t) else pos[O(53)] + f
    if b == 57: return pos[B(54)] if 'tbmm' in t else pos[B(53)]
    if b == 59 and 'merkez' in t: return pos[B(65)]
    return round(M[b] + f, 4)
if __name__ == '__main__':
    out = L
    def put(name, val):
        global out
        i = out.index(name + '=') + len(name) + 1; _, e = json.JSONDecoder().raw_decode(out[i:]); out = out[:i] + json.dumps(val, ensure_ascii=False) + out[i + e:]
    K = span('K0')[2]
    for x in K: x[2] = m(x[2], x[1])
    G = span('GMC')[2]
    for r in G['rows']: r['r'] = m(r['r'], r['u'])
    C = span('C90')[2]
    for sc in C['sections']: sc['r'] = m(sc['r'], sc['t'])
    O2 = span('O2N')[2]
    O2 = {k: m(v) for k, v in O2.items()}
    put('RS', NEW); put('K0', K); put('GMC', G); put('C90', C); put('O2N', O2)
    lines[LN] = out
    # cihazda kayıtlı eski numaralar için geçiş tablosu
    tab = {str(k): m(k) for k in range(50, 210)}
    s2 = '\n'.join(lines)
    s2 = s2.replace('const o2n=', 'const R11=' + json.dumps(tab) + ',r11=r=>{r=+r;if(!(r>=50)||r>=300)return r;const b=Math.floor(r),f=Math.round((r-b)*1e4)/1e4;if(b===51)return f>0.15?' + str(pos[B(69)]) + ':' + str(pos[B(55)]) + ';return R11[b]!=null?Math.round((R11[b]+(b===53?f:f))*1e4)/1e4:r};\nconst o2n=', 1)
    open(P, 'w', encoding='utf-8').write(s2)
    print('yeni liste', len(NEW), 'madde'); print(json.dumps({k: m(k) for k in (50, 51, 53, 58, 59, 60, 61, 62, 71, 81, 82, 91, 92, 122, 209)}))
