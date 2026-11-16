"""Onaylanmış paketi korur, sonradan eklenenleri ayrı onay paketine ayırır.
Kullanım: python3 tools/rehber/paket_ayir.py <onaylı_paket.json> <tam_paket.json> <yeni_id>
 - data/rehber.json   : onaylı paket (yalnızca sıra numaraları yeni listeye taşınır)
 - data/rehber-2.json : onaylı pakette olmayan kayıtlar (onay bekler)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from rical_sayfa2 import m
A = json.load(open(sys.argv[1], encoding='utf-8')); T = json.load(open(sys.argv[2], encoding='utf-8'))
if not A.get('rs2'):   # eski numaralı onaylı paket -> yeni numaralar
    for k in ('ekle', 'guncelle', 'eskit'):
        for e in A[k]: e['r'] = m(e['r'], e.get('t_new') or e.get('t'))
    A['rs2'] = 1
A['id'] = A.get('id') or 'rh-' + A['tarih']
ka = lambda e: (e['n'], e.get('t') or e.get('t_old'), e.get('t_new', ''))
have = {ka(e) for k in ('ekle', 'guncelle', 'eskit') for e in A[k]}
chain = {(e['n'], e['t_old']): e['t_new'] for k in ('guncelle', 'eskit') for e in A[k]}
B = {'id': sys.argv[3], 'tarih': T['tarih'], 'kaynaklar': T['kaynaklar'], 'rs2': 1, 'ekle': [], 'guncelle': [], 'eskit': []}
seen_ekle = {(e['n'], e['t']) for e in A['ekle']}
for k in ('ekle', 'guncelle', 'eskit'):
    for e in T[k]:
        if ka(e) in have: continue
        if k == 'ekle':
            if (e['n'], e['t']) in seen_ekle: continue
            B[k].append(e); continue
        e = dict(e)
        if (e['n'], e['t_old']) in chain:
            if chain[(e['n'], e['t_old'])] == e['t_new']: continue
            e['t_old'] = chain[(e['n'], e['t_old'])]
        B[k].append(e)
json.dump(A, open('data/rehber.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(B, open('data/rehber-2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
from collections import Counter
for k in ('ekle', 'guncelle', 'eskit'): print(k, len(B[k]), dict(Counter(e['kat'] for e in B[k])))
