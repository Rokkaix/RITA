"""İki fotolar.json'u birleştirir (çakışmada veri kaybı olmasın): fotoğrafı olan kayıt, olmayana üstün;
ikisinde de varsa daha yeni tarihli olan. Kullanım: python3 tools/fotolar_birlestir.py hedef.json kaynak.json [kaynak2.json ...]"""
import json, sys
def oku(p):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return {}
hedef = sys.argv[1]; D = oku(hedef)
for p in sys.argv[2:]:
    for k, v in oku(p).items():
        e = D.get(k)
        if e is None or (v.get('u') and not e.get('u')) or (bool(v.get('u')) == bool(e.get('u')) and v.get('d', '') > e.get('d', '')): D[k] = v
json.dump(dict(sorted(D.items())), open(hedef, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('birleşti:', len(D), 'kayıt,', sum(1 for v in D.values() if v.get('u')), 'fotoğraf')
