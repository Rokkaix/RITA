/* RITA bildirim sunucusu (Cloudflare Worker, ücretsiz plan).
   - POST /abone   {kod, sub}            : personelin telefonu kendi koduyla push aboneliğini kaydeder.
   - POST /gonder  {kod, t, b, u, s}     : yönetici (GitHub anahtarıyla doğrulanır) o koda bildirim gönderir.
   - GET  /        : durum + VAPID açık anahtarı.
   Abonelikler KV'de (RITA_ABONE) tutulur; personel adı/telefonu ASLA buraya gelmez — yalnız rastgele kod.
   Web Push: VAPID (RFC 8292) + aes128gcm şifreleme (RFC 8291), yalnız WebCrypto ile. */
const IZINLI = ['https://rokkaix.github.io'];
const REPO = 'Rokkaix/RITA';
const te = new TextEncoder();
const b64u = b => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64ud = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), c => c.charCodeAt(0));
const birlestir = (...a) => { const o = new Uint8Array(a.reduce((t, x) => t + x.length, 0)); let i = 0; for (const x of a) { o.set(x, i); i += x.length } return o };
async function hkdf(salt, ikm, info, len) {
  const k = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'HKDF', hash: 'SHA-256', salt, info }, k, len * 8));
}
async function vapidBaslik(endpoint, env) {
  const jwk = JSON.parse(env.VAPID_JWK);
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const h = b64u(te.encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const c = b64u(te.encode(JSON.stringify({ aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: 'https://rokkaix.github.io/RITA/' })));
  const imza = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, te.encode(h + '.' + c));
  return 'vapid t=' + h + '.' + c + '.' + b64u(imza) + ', k=' + env.VAPID_PUBLIC;
}
async function sifrele(sub, metin) {
  const uaPub = b64ud(sub.keys.p256dh), auth = b64ud(sub.keys.auth);
  const es = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asPub = new Uint8Array(await crypto.subtle.exportKey('raw', es.publicKey));
  const uaKey = await crypto.subtle.importKey('raw', uaPub, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const ecdh = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: uaKey }, es.privateKey, 256));
  const ikm = await hkdf(auth, ecdh, birlestir(te.encode('WebPush: info\0'), uaPub, asPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, te.encode('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, te.encode('Content-Encoding: nonce\0'), 12);
  const k = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, k, birlestir(te.encode(metin), new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]);
  return birlestir(salt, rs, new Uint8Array([asPub.length]), asPub, ct);
}
async function pushGonder(sub, veri, env, acil) {
  const govde = await sifrele(sub, JSON.stringify(veri));
  return fetch(sub.endpoint, { method: 'POST', body: govde, headers: {
    Authorization: await vapidBaslik(sub.endpoint, env), 'Content-Encoding': 'aes128gcm', 'Content-Type': 'application/octet-stream', TTL: '7200', Urgency: acil ? 'high' : 'normal' } });
}
async function yoneticiMi(tok, env) {
  if (!tok) return false;
  const iz = b64u(await crypto.subtle.digest('SHA-256', te.encode(tok)));
  if (await env.RITA_ABONE.get('a:' + iz)) return true;
  const r = await fetch('https://api.github.com/repos/' + REPO, { headers: { Authorization: 'Bearer ' + tok, 'User-Agent': 'rita-bildirim', Accept: 'application/vnd.github+json' } });
  if (!r.ok) return false;
  const j = await r.json();
  if (!(j.permissions && j.permissions.push)) return false;
  await env.RITA_ABONE.put('a:' + iz, '1', { expirationTtl: 3600 });
  return true;
}
const KOD = /^[A-Za-z0-9]{8,32}$/;
export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '';
    const cors = { 'Access-Control-Allow-Origin': IZINLI.includes(o) ? o : IZINLI[0], 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-GH-Token', 'Vary': 'Origin' };
    const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const yol = new URL(req.url).pathname;
    try {
      if (req.method === 'GET') return json({ rita: 'bildirim', vapid: env.VAPID_PUBLIC });
      const g = await req.json();
      if (yol === '/abone') {
        if (!KOD.test(g.kod || '') || !g.sub || !/^https:\/\//.test(g.sub.endpoint || '') || !g.sub.keys) return json({ hata: 'geçersiz' }, 400);
        const iz = b64u(await crypto.subtle.digest('SHA-256', te.encode(g.sub.endpoint))).slice(0, 16);
        await env.RITA_ABONE.put('s:' + g.kod + ':' + iz, JSON.stringify({ endpoint: g.sub.endpoint, keys: g.sub.keys }), { expirationTtl: 60 * 60 * 24 * 180 });
        if (g.selam) await pushGonder(g.sub, { t: 'RITA bildirimleri açık ✓', b: 'Yeni görevler bu telefona bildirim olarak gelecek.', u: g.u || '' }, env, true);
        return json({ tamam: true });
      }
      if (yol === '/gonder') {
        if (!(await yoneticiMi(req.headers.get('X-GH-Token'), env))) return json({ hata: 'yetkisiz' }, 401);
        if (!KOD.test(g.kod || '')) return json({ hata: 'geçersiz kod' }, 400);
        const L = await env.RITA_ABONE.list({ prefix: 's:' + g.kod + ':' });
        let ok = 0, silinen = 0;
        for (const k of L.keys) {
          const sub = JSON.parse(await env.RITA_ABONE.get(k.name) || 'null'); if (!sub) continue;
          const r = await pushGonder(sub, { t: String(g.t || '').slice(0, 120), b: String(g.b || '').slice(0, 240), u: g.u || '', tag: g.tag || '', s: g.s ? 1 : 0 }, env, !g.s);
          if (r.status === 404 || r.status === 410) { await env.RITA_ABONE.delete(k.name); silinen++ } else if (r.ok) ok++;
        }
        return json({ cihaz: L.keys.length, gonderilen: ok, silinen });
      }
      return json({ hata: 'yok' }, 404);
    } catch (e) { return json({ hata: String(e && e.message || e) }, 500) }
  }
};
