/* =====================================================================
   RITA Quick Check Okuyucu — arka.js (service worker)
   quick.js'ten gelen okumaları RITA Canlı sayfasına (program.js bağlantısına) iletir.
   Veri yalnız bellekte durur; diske, depolamaya ya da sunucuya YAZILMAZ.
   Hiçbir izin (permissions / host_permissions) gerektirmez.
   ===================================================================== */
"use strict";

/* Her Quick Check sekmesi için birleşik durum: { ucus, yolcular:{k:y}, sira:[k], koltuklar:{}, zaman } */
const durum = new Map();
/* Bağlı RITA sayfaları (program.js portları) */
const ritaPortlari = new Set();

function sekmeDurumu(id) {
  if (!durum.has(id)) durum.set(id, { ucus: null, yolcular: {}, sira: [], koltuklar: {}, zaman: 0 });
  return durum.get(id);
}

function herkese(mesaj) {
  for (const p of ritaPortlari) { try { p.postMessage(mesaj); } catch (e) { ritaPortlari.delete(p); } }
}

function tamGoruntu(id) {
  const d = durum.get(id);
  return { tur: "tam", sekme: id, ucus: d.ucus, yolcular: d.sira.map((k) => d.yolcular[k]).filter(Boolean), koltuklar: d.koltuklar, zaman: d.zaman };
}

/* Farkları birleşik duruma uygula (yeni bağlanan RITA sayfasına tam görüntü verebilmek için) */
function uygula(d, F) {
  for (const f of F) {
    if (f.tip === "eklendi" && f.yolcu) { d.yolcular[f.k] = f.yolcu; if (!d.sira.includes(f.k)) d.sira.push(f.k); }
    else if (f.tip === "cikti") { delete d.yolcular[f.k]; d.sira = d.sira.filter((k) => k !== f.k); }
    else if (f.tip === "sira" && Array.isArray(f.sira)) d.sira = f.sira.slice();
    else if (f.tip === "koltukDurum") d.koltuklar[f.koltuk] = f.yeni;
    else if (d.yolcular[f.k]) {
      const alan = { koltuk: "koltuk", checkin: "ci", not: "not", sinif: "sinif" }[f.tip];
      if (alan) d.yolcular[f.k][alan] = f.yeni;
    }
  }
}

chrome.runtime.onMessage.addListener((m, gonderen, yanitla) => {
  if (!m || m.rita !== 1 || !gonderen.tab) return;                      /* yalnız kendi içerik betiğimiz */
  if (!/^https:\/\/checkin\.thy\.com\/V1\//.test(gonderen.url || "")) return;
  const id = gonderen.tab.id, ilk = !durum.has(id), d = sekmeDurumu(id);
  if (m.ucus && m.ucus.no) {
    if (d.ucus && (d.ucus.no !== m.ucus.no || d.ucus.tarih !== m.ucus.tarih)) { d.yolcular = {}; d.sira = []; d.koltuklar = {}; }
    d.ucus = m.ucus;
  }
  d.zaman = m.zaman || Date.now();

  if (m.tur === "tam") {
    if (Array.isArray(m.yolcular)) { d.yolcular = {}; d.sira = []; m.yolcular.forEach((y) => { d.yolcular[y.k] = y; d.sira.push(y.k); }); }
    if (m.koltuklar) d.koltuklar = Object.assign({}, m.koltuklar);
    herkese(tamGoruntu(id));
    yanitla({ ok: 1 });
    return;
  }
  /* arka plan yeniden başladıysa (bellek boş) içerik betiğinden tam görüntü iste */
  if (ilk) { yanitla({ tamIste: true }); return; }
  if (m.tur === "fark" && Array.isArray(m.farklar)) {
    uygula(d, m.farklar);
    herkese({ tur: "fark", sekme: id, ucus: d.ucus, farklar: m.farklar, zaman: d.zaman });
  } else if (m.tur === "nabiz") {
    herkese({ tur: "nabiz", sekme: id, ucus: d.ucus, zaman: d.zaman });
  }
  yanitla({ ok: 1 });
});

/* RITA sayfası (program.js) bağlanınca bilinen tüm uçuşların tam görüntüsünü gönder */
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "rita") return;
  const url = (port.sender && port.sender.url) || "";
  if (!/^https:\/\/rokkaix\.github\.io\/RITA\//.test(url)) { port.disconnect(); return; }
  ritaPortlari.add(port);
  port.onDisconnect.addListener(() => ritaPortlari.delete(port));
  port.postMessage({ tur: "merhaba", surum: chrome.runtime.getManifest().version, zaman: Date.now() });
  for (const id of durum.keys()) port.postMessage(tamGoruntu(id));
});

/* Quick Check sekmesi kapanınca o sekmenin verisini bellekten sil */
chrome.tabs.onRemoved.addListener((id) => { if (durum.delete(id)) herkese({ tur: "kapandi", sekme: id, zaman: Date.now() }); });
