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
async function koda(env, kod, veri, acil) {
  const L = await env.RITA_ABONE.list({ prefix: 's:' + kod + ':' }); let ok = 0, silinen = 0;
  for (const k of L.keys) {
    const sub = JSON.parse(await env.RITA_ABONE.get(k.name) || 'null'); if (!sub) continue;
    const r = await pushGonder(sub, veri, env, acil);
    if (r.status === 404 || r.status === 410) { await env.RITA_ABONE.delete(k.name); silinen++ } else if (r.ok) ok++;
  }
  return { cihaz: L.keys.length, gonderilen: ok, silinen };
}
/* ---- canlı uçuş durumu (FlightStats; yalnız THY 'TK' uçuşları) ---- */
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36';
const DURUM = { S: 'Planlandı', A: 'Havada', L: 'İndi', C: 'İptal', D: 'Yönlendirildi', R: 'Yönlendirildi', U: 'Bilinmiyor', NO: 'Uçmadı' };
function nextData(h) {
  const i = h.indexOf('__NEXT_DATA__ = '); if (i < 0) return null;
  let j = i + 16, d = 0, str = false, esc = false;
  for (; j < h.length; j++) { const c = h[j];
    if (str) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') str = false; continue }
    if (c === '"') str = true; else if (c === '{') d++; else if (c === '}') { d--; if (d === 0) { j++; break } } }
  return JSON.parse(h.slice(i + 16, j));
}
async function ucusDurumu(no, gun, yon) {
  const m = /^TK(\d{1,4})$/.exec(no || ''), g = /^(\d{4})-(\d{2})-(\d{2})$/.exec(gun || ''); if (!m || !g) return null;
  const r = await fetch('https://www.flightstats.com/v2/flight-tracker/TK/' + m[1] + '?year=' + g[1] + '&month=' + (+g[2]) + '&date=' + (+g[3]), { headers: { 'User-Agent': UA }, cf: { cacheTtl: 60 } });
  if (!r.ok) return { hata: 'kaynak ' + r.status };
  const F = ((((nextData(await r.text()) || {}).props || {}).initialState || {}).flightTracker || {}).flight; if (!F) return { hata: 'bulunamadı' };
  const st = F.status || {}, dep = F.departureAirport || {}, arr = F.arrivalAirport || {};
  const ist = yon === 'gelis' ? arr : dep, t = x => ((x || {}).times || {});
  return { kod: st.statusCode || '', durum: DURUM[st.statusCode] || st.status || '', yon,
    kalkis: { apt: dep.iata || dep.fs || '', plan: (t(dep).scheduled || {}).time24 || '', tahmini: (t(dep).estimatedActual || {}).time24 || '', tur: (t(dep).estimatedActual || {}).title || '', kapi: dep.gate || '', terminal: dep.terminal || '' },
    inis: { apt: arr.iata || arr.fs || '', plan: (t(arr).scheduled || {}).time24 || '', tahmini: (t(arr).estimatedActual || {}).time24 || '', tur: (t(arr).estimatedActual || {}).title || '', kapi: arr.gate || '', terminal: arr.terminal || '', bant: arr.baggage || '' },
    kapi: ist.gate || '', bant: arr.baggage || '', zaman: new Date().toISOString() };
}
/* "HH:MM" İstanbul saatini, uçuş gününe göre zaman damgasına çevir (gece yarısı geçişi dahil) */
function anDk(gun, hhmm) { if (!/^\d{1,2}:\d{2}$/.test(hhmm || '')) return null; let t = Date.parse(gun + 'T' + hhmm.padStart(5, '0') + ':00+03:00'); const now = Date.now();
  if (t - now > 14 * 3600e3) t -= 864e5; else if (now - t > 14 * 3600e3) t += 864e5; return Math.round((t - now) / 60000) }
/* izlenen (atanmış) uçuşları kontrol et: kapı değişikliği, saat değişikliği, iptal, kalkış, yaklaşma, iniş */
async function izlemeTur(env) {
  const L = JSON.parse(await env.RITA_ABONE.get('izleme') || '[]'); if (!L.length) return;
  const bugun = new Date(Date.now() + 3 * 3600e3).toISOString().slice(0, 10), dun = new Date(Date.now() - 21 * 3600e3).toISOString().slice(0, 10);
  let degisti = false; const kalan = [];
  for (const it of L) {
    if (it.gun < dun) { degisti = true; continue } kalan.push(it);
    if (it.son && it.son.bitti) continue;
    const d = await ucusDurumu(it.no, it.gun, it.yon).catch(() => null); if (!d || d.hata) continue;
    const s = it.son || {}, ev = [], baslik = '[' + it.no + (it.hat ? ' | ' + it.hat.replace('-', ' - ') : '') + '] ';
    const yer = it.yon === 'gelis' ? d.inis : d.kalkis, tah = yer.tahmini || yer.plan;
    if (d.kapi && d.kapi !== s.kapi && !(it.elle && it.elle.kapi)) ev.push([s.kapi ? 'Kapı değişti: ' + s.kapi + ' → ' + d.kapi : 'Kapı belli oldu: ' + d.kapi, (it.yon === 'gelis' ? 'Geliş' : 'Gidiş') + ' · ' + (tah ? 'tahmini ' + tah : ''), true]);
    if (!(it.yon === 'gelis' && d.kod === 'A') && s.tah && tah && s.tah !== tah && Math.abs((anDk(it.gun, tah) ?? 0) - (anDk(it.gun, s.tah) ?? 0)) >= 10) ev.push(['Saat değişti: tahmini ' + tah, 'Planlanan ' + (yer.plan || '-') + (d.kapi ? ' · Kapı ' + d.kapi : ''), true]);
    if (d.kod === 'C' && !s.iptal) { ev.push(['İPTAL', 'Uçuş iptal edildi', true]); s.iptal = 1 }
    if (it.yon === 'gidis' && d.kod === 'A' && !s.kalkti) { ev.push(['Kalktı', 'Uçak havalandı' + (d.kalkis.tahmini ? ' · ' + d.kalkis.tahmini : ''), false]); s.kalkti = 1; s.bitti = 1 }
    if (it.yon === 'gelis') {
      const kal = anDk(it.gun, d.inis.tahmini || d.inis.plan);
      if (d.kod === 'A' && kal != null && kal <= 30 && kal > 10 && !s.y30) { ev.push(['Yaklaşıyor: ~' + kal + ' dk sonra iniş', 'Tahmini iniş ' + (d.inis.tahmini || d.inis.plan) + (d.kapi ? ' · Kapı ' + d.kapi : '') + ' · karşılamaya hazırlanın', true]); s.y30 = 1 }
      if (d.kod === 'A' && kal != null && kal <= 10 && !s.y10) { ev.push(['İnişe geçti: ~' + Math.max(kal, 1) + ' dk', (d.kapi ? 'Kapı ' + d.kapi : 'Kapı henüz belli değil') + ' · tahmini ' + (d.inis.tahmini || d.inis.plan), true]); s.y10 = s.y30 = 1 }
      if (d.kod === 'L' && !s.indi) { ev.push(['İndi', (d.kapi ? 'Kapı ' + d.kapi : '') + (d.bant ? ' · Bant ' + d.bant : '') + (d.inis.tahmini ? ' · ' + d.inis.tahmini : ''), true]); s.indi = s.y10 = s.y30 = 1 }
      if (d.bant && s.indi && d.bant !== s.bant && s.bant) ev.push(['Bagaj bandı: ' + d.bant, '', false]);
      if (d.kod === 'L' && d.bant && (s.indi || ev.length)) s.bitti = 1;
    }
    if (d.kapi !== s.kapi || tah !== s.tah || d.bant !== s.bant || ev.length) { degisti = true; it.son = { ...s, kapi: d.kapi, tah, bant: d.bant, kod: d.kod } }
    if (ev.length) {  // aynı turdaki olaylar tek bildirimde birleşir
      const acil = ev.some(e => e[2]), t = baslik + ev.map(e => e[0]).join(' · '), b = ev.map(e => e[1]).filter(Boolean)[0] || '';
      for (const k of it.kodlar || []) await koda(env, k, { t: t.slice(0, 120), b, u: it.u || '', tag: it.id, s: acil ? 0 : 1 }, acil).catch(() => {});
    }
  }
  if (degisti) await env.RITA_ABONE.put('izleme', JSON.stringify(kalan));
}
export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '';
    const cors = { 'Access-Control-Allow-Origin': IZINLI.includes(o) ? o : IZINLI[0], 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-GH-Token', 'Vary': 'Origin' };
    const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const yol = new URL(req.url).pathname;
    try {
      if (req.method === 'GET' && yol === '/ucus') {  // canlı uçuş durumu (herkese açık bilgi; yalnız TK)
        const q = new URL(req.url).searchParams; return json(await ucusDurumu(q.get('no'), q.get('gun'), q.get('yon') === 'gelis' ? 'gelis' : 'gidis') || { hata: 'geçersiz' });
      }
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
        return json(await koda(env, g.kod, { t: String(g.t || '').slice(0, 120), b: String(g.b || '').slice(0, 240), u: g.u || '', tag: g.tag || '', s: g.s ? 1 : 0 }, !g.s));
      }
      if (yol === '/izle' || yol === '/izle-sil' || yol === '/izlenen') {  // atanmış uçuş takibi (yönetici)
        if (!(await yoneticiMi(req.headers.get('X-GH-Token'), env))) return json({ hata: 'yetkisiz' }, 401);
        let L = JSON.parse(await env.RITA_ABONE.get('izleme') || '[]');
        if (yol === '/izlenen') return json(L);
        L = L.filter(x => x.id !== g.id);
        if (yol === '/izle') {
          if (!/^[A-Za-z0-9_-]{1,40}$/.test(g.id || '') || !/^TK\d{1,4}$/.test(g.no || '') || !/^\d{4}-\d{2}-\d{2}$/.test(g.gun || '')) return json({ hata: 'geçersiz' }, 400);
          const eski = JSON.parse(await env.RITA_ABONE.get('izleme') || '[]').find(x => x.id === g.id) || {};
          L.push({ id: g.id, no: g.no, gun: g.gun, yon: g.yon === 'gelis' ? 'gelis' : 'gidis', hat: String(g.hat || '').slice(0, 9), u: String(g.u || '').slice(0, 300),
            kodlar: (g.kodlar || []).filter(k => KOD.test(k)).slice(0, 6), elle: g.elle || null, son: eski.son || null });
        }
        await env.RITA_ABONE.put('izleme', JSON.stringify(L.slice(-60)));
        return json({ tamam: true, sayi: L.length });
      }
      return json({ hata: 'yok' }, 404);
    } catch (e) { return json({ hata: String(e && e.message || e) }, 500) }
  },
  async scheduled(ev, env, ctx) { ctx.waitUntil(izlemeTur(env)) }
};
