"""RITA bildirim sunucusunu Cloudflare'e kurar/günceller (ücretsiz Workers + KV).
Cloudflare API anahtarı ortamdan (ağ vekili) eklenir; VAPID gizli anahtarı yalnız Worker'a 'secret' olarak yüklenir, depoya yazılmaz.
Kullanım: python3 worker/kur.py <vapid.json yolu>"""
import json, sys, os, uuid, urllib.request, urllib.error, secrets
API = 'https://api.cloudflare.com/client/v4'
def cf(yol, yontem='GET', veri=None, tur='application/json', ham=None):
    h = {'Authorization': 'Bearer proxy-injected'}
    govde = ham if ham is not None else (json.dumps(veri).encode() if veri is not None else None)
    if govde is not None: h['Content-Type'] = tur
    try:
        with urllib.request.urlopen(urllib.request.Request(API + yol, data=govde, method=yontem, headers=h), timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: return json.load(e)
V = json.load(open(sys.argv[1]))
acc = cf('/accounts')
if not acc.get('success') or not acc['result']: sys.exit('Cloudflare hesabı okunamadı: ' + json.dumps(acc.get('errors')))
aid = acc['result'][0]['id']; print('hesap:', acc['result'][0]['name'])
sd = cf('/accounts/%s/workers/subdomain' % aid)
alt = (sd.get('result') or {}).get('subdomain')
if not alt:
    alt = 'rita-' + secrets.token_hex(3); r = cf('/accounts/%s/workers/subdomain' % aid, 'PUT', {'subdomain': alt})
    if not r.get('success'): sys.exit('workers.dev alt alan adı alınamadı: ' + json.dumps(r.get('errors')))
print('alt alan:', alt)
ns = cf('/accounts/%s/storage/kv/namespaces?per_page=100' % aid)
nid = next((n['id'] for n in ns.get('result') or [] if n['title'] == 'RITA_ABONE'), None)
if not nid:
    r = cf('/accounts/%s/storage/kv/namespaces' % aid, 'POST', {'title': 'RITA_ABONE'})
    if not r.get('success'): sys.exit('KV oluşturulamadı: ' + json.dumps(r.get('errors')))
    nid = r['result']['id']
kod = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rita-bildirim.js'), encoding='utf-8').read()
meta = {'main_module': 'rita-bildirim.js', 'compatibility_date': '2026-11-01',
        'bindings': [{'type': 'kv_namespace', 'name': 'RITA_ABONE', 'namespace_id': nid},
                     {'type': 'plain_text', 'name': 'VAPID_PUBLIC', 'text': V['pub']},
                     {'type': 'secret_text', 'name': 'VAPID_JWK', 'text': json.dumps(V['jwk'])}]}
b = uuid.uuid4().hex
parca = ('--%s\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n%s\r\n'
         '--%s\r\nContent-Disposition: form-data; name="rita-bildirim.js"; filename="rita-bildirim.js"\r\nContent-Type: application/javascript+module\r\n\r\n%s\r\n--%s--\r\n') % (b, json.dumps(meta), b, kod, b)
r = cf('/accounts/%s/workers/scripts/rita-bildirim' % aid, 'PUT', ham=parca.encode('utf-8'), tur='multipart/form-data; boundary=' + b)
if not r.get('success'): sys.exit('Worker yüklenemedi: ' + json.dumps(r.get('errors')))
r = cf('/accounts/%s/workers/scripts/rita-bildirim/subdomain' % aid, 'POST', {'enabled': True})
print('workers.dev:', r.get('success'), r.get('errors') or '')
r = cf('/accounts/%s/workers/scripts/rita-bildirim/schedules' % aid, 'PUT', [{'cron': '*/2 * * * *'}])
print('zamanlayıcı (2 dk):', r.get('success'), r.get('errors') or '')
print('ADRES https://rita-bildirim.%s.workers.dev' % alt)
