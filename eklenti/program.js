/* =====================================================================
   RITA Quick Check Okuyucu — program.js (RITA sayfasında çalışan içerik betiği)
   arka.js ile bağlantı kurar ve gelen veriyi window.postMessage ile RITA sayfasına aktarır.
   Sayfaya yalnız aynı kökene (rokkaix.github.io) mesaj gönderir; sayfadan komut ALMAZ.
   ===================================================================== */
(function () {
  "use strict";
  const KOK = location.origin;               /* https://rokkaix.github.io */
  let port = null, bekleme = 1000;

  function sayfaya(veri) {
    window.postMessage(Object.assign({ kaynak: "eklenti" }, veri), KOK);
  }

  function baglan() {
    try { port = chrome.runtime.connect({ name: "rita" }); }
    catch (e) { return; }                     /* eklenti kaldırıldı / güncellendi */
    bekleme = 1000;
    port.onMessage.addListener((m) => { if (m && typeof m.tur === "string") sayfaya(m); });
    port.onDisconnect.addListener(() => {
      port = null;
      sayfaya({ tur: "baglantiKoptu", zaman: Date.now() });
      /* service worker uyuyup uyanabilir: artan aralıkla yeniden bağlan */
      setTimeout(baglan, bekleme);
      bekleme = Math.min(bekleme * 2, 15000);
    });
  }

  baglan();
})();
