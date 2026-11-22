/* =====================================================================
   RITA Quick Check Okuyucu — quick.js (içerik betiği)
   Quick Check sayfasında (ve iframe'lerinde) çalışır. YALNIZCA OKUR:
   hiçbir alana yazmaz, hiçbir şeye tıklamaz, sayfayı yenilemez, giriş yapmaz.
   Okuduğu veriyi yalnız kendi eklentisinin arka planına (arka.js) gönderir.
   ===================================================================== */

/* ---------------------------------------------------------------------
   CONFIG — gerçek sayfaya uyarlamak için YALNIZ bu bölümü değiştirin.
   (Nasıl yapılacağı: eklenti/BENIOKU.md → "CONFIG'i gerçek sayfaya uyarlama")
   --------------------------------------------------------------------- */
const CONFIG = {
  quickCheckUrl: "https://checkin.thy.com/V1/Pages/Default.aspx",

  /* Uçuş başlığı: "Uçuş: TK2150 / 22NOV". Başlığı içeren öğe için seçici (boşsa tüm sayfa metni taranır). */
  ucusBaslikSecici: "",
  ucusRegex: /U[çc]u[şs]\s*:\s*(TK\s?\d{2,5})\s*\/\s*(\d{1,2}[A-ZĞÜŞİÖÇ]{3})/i,

  /* ---- Yolcu listesi ----
     satirSecici: yolcu satırlarını seçen CSS seçicisi. Varsayılan "tr" — sayfadaki tüm tablo satırları;
     başlık satırı aşağıdaki başlık adlarıyla bulunur ve sütun sırası OTOMATİK çıkarılır.
     Otomatik bulma tutmazsa "sutunlar" ile elle sütun sırası verin (0'dan başlar) ve otomatikBaslik:false yapın. */
  satirSecici: "tr",
  otomatikBaslik: true,
  baslikAdlari: {            /* başlık hücresindeki yazı (büyük/küçük harf, Türkçe harf fark etmez) */
    klt: ["klt", "koltuk"],
    cl: ["cl", "ci"],
    s: ["s"],
    soyad: ["soyad"],
    ad: ["ad"],
    c: ["c", "comment", "aciklama"],
    gk: ["gk"]
  },
  sutunlar: { sira: 0, pnr: 1, gk: 2, klt: 3, ct: 4, guv: 5, cl: 6, s: 7, soyad: 8, ad: 9, c: 10 },
  enAzHucre: 6,              /* bundan az hücreli satırlar yolcu satırı sayılmaz */
  yalnizVip: true,           /* true: yalnız açıklaması "!VIP!" içeren satırlar alınır */
  vipIsareti: "!VIP!",
  /* check-in hücresi: içinde resim/simge veya bu işaretlerden biri varsa "check-in yapılmış" sayılır */
  checkinIsaretleri: ["✔", "✓", "√", "OK", "Y"],

  /* ---- Koltuk haritası ----
     koltukHucreSecici: koltuk kutularını seçen CSS seçicisi. Varsayılan "td" — yazısı koltuk koduna
     benzeyen (01A, 12C…) tüm hücreler koltuk sayılır. Renk, hücrenin arka plan renginden okunur. */
  koltukHucreSecici: "td",
  koltukRegex: /^\s*0?(\d{1,2})([A-K])\s*$/,
  enAzKoltuk: 12,            /* bir sayfada bundan az koltuk bulunursa koltuk haritası yok sayılır */

  /* ---- Akış ---- */
  taramaMs: 2000,            /* yeniden okuma aralığı (ms) */
  degisimBekleMs: 300,       /* sayfa değişince (MutationObserver) okumadan önce bekleme */
  hataAyikla: false          /* true: her okumada konsola ayrıntı yazar */
};
/* ------------------------------ CONFIG SONU ------------------------------ */

(function () {
  "use strict";

  /* Güvenlik: giriş/şifre sayfalarında asla çalışma (manifest zaten hariç tutar; bu ikinci kilittir). */
  const yer = location.href;
  if (/\/Login\.aspx/i.test(yer) || /auth\.thy\.com/i.test(location.hostname)) return;
  if (document.querySelector('input[type="password"]')) return;

  const ETIKET = "[RITA okuyucu]";
  const log = (...a) => { if (CONFIG.hataAyikla) console.log(ETIKET, ...a); };
  const uyar = (() => { const gorulen = new Set(); return (m) => { if (!gorulen.has(m)) { gorulen.add(m); console.warn(ETIKET, m); } }; })();

  /* Türkçe → sade büyük harf (karşılaştırma için) */
  const sade = (t) => String(t || "").replace(/\s+/g, " ").trim()
    .replace(/[iı]/g, (c) => (c === "i" ? "İ" : "I")).toUpperCase()
    .replace(/İ/g, "I").replace(/Ş/g, "S").replace(/Ğ/g, "G").replace(/Ü/g, "U").replace(/Ö/g, "O").replace(/Ç/g, "C");
  const hucreMetni = (td) => (td ? String(td.textContent || "").replace(/\s+/g, " ").trim() : "");

  /* ---------------- Uçuş başlığı ---------------- */
  function ucusOku() {
    const kok = CONFIG.ucusBaslikSecici ? document.querySelector(CONFIG.ucusBaslikSecici) : document.body;
    if (!kok) return null;
    const m = String(kok.innerText || kok.textContent || "").match(CONFIG.ucusRegex);
    return m ? { no: m[1].replace(/\s+/g, "").toUpperCase(), tarih: m[2].toUpperCase() } : null;
  }

  /* ---------------- Yolcu listesi ---------------- */
  function sutunBul(satirlar) {
    if (!CONFIG.otomatikBaslik) return { harita: CONFIG.sutunlar, baslik: null };
    for (const tr of satirlar) {
      const H = Array.from(tr.children).map((h) => sade(hucreMetni(h)).toLowerCase());
      if (!H.some((x) => CONFIG.baslikAdlari.soyad.includes(x))) continue;
      const harita = {};
      for (const [anahtar, adlar] of Object.entries(CONFIG.baslikAdlari)) {
        const i = H.findIndex((x) => adlar.includes(x));
        if (i >= 0) harita[anahtar] = i;
      }
      if (harita.soyad != null && harita.klt != null) return { harita, baslik: tr };
    }
    return null;
  }

  function checkinMi(td) {
    if (!td) return false;
    if (td.querySelector("img,svg,i,span[class*='check' i],span[class*='ok' i]")) return true;
    const t = hucreMetni(td).toUpperCase();
    return CONFIG.checkinIsaretleri.some((x) => t.includes(x.toUpperCase()));
  }

  function koltukNormal(t) {
    const m = String(t || "").toUpperCase().match(CONFIG.koltukRegex);
    return m ? String(parseInt(m[1], 10)) + m[2] : "";
  }

  function yolculariOku() {
    const satirlar = Array.from(document.querySelectorAll(CONFIG.satirSecici));
    if (!satirlar.length) return null;
    const S = sutunBul(satirlar);
    if (!S) { log("bu çerçevede yolcu listesi başlığı yok"); return null; }
    const h = S.harita, liste = [];
    const basla = S.baslik ? satirlar.indexOf(S.baslik) + 1 : 0;
    for (const tr of satirlar.slice(basla)) {
      const td = Array.from(tr.children);
      if (td.length < CONFIG.enAzHucre) continue;
      const soyad = hucreMetni(td[h.soyad]).replace(/[^A-Za-zÇĞİÖŞÜçğıöşü' -]/g, "").trim();
      if (!soyad) continue;
      const not = h.c != null ? hucreMetni(td[h.c]) : "";
      if (CONFIG.yalnizVip && !sade(not).includes(sade(CONFIG.vipIsareti))) continue;
      const ad = h.ad != null ? hucreMetni(td[h.ad]) : "";
      const sinif = h.s != null ? hucreMetni(td[h.s]).toUpperCase().slice(0, 1) : "";
      const gk = h.gk != null ? hucreMetni(td[h.gk]).slice(0, 6) : "";
      const y = {
        soyad: soyad.toUpperCase().slice(0, 40),
        adBas: ad ? ad.trim().charAt(0).toUpperCase() : "",   /* yalnız ad baş harfi */
        koltuk: koltukNormal(hucreMetni(td[h.klt])),
        ci: h.cl != null ? checkinMi(td[h.cl]) : false,
        sinif: /^[A-Z]$/.test(sinif) ? sinif : "",
        not: not.slice(0, 300)
      };
      /* kimlik: soyad + ad baş harfi + grup kodu (PNR gönderilmez) */
      y.k = [y.soyad, y.adBas, gk].join("|");
      liste.push(y);
    }
    if (!liste.length) uyar("Yolcu listesi başlığı bulundu ama VIP satır okunamadı. CONFIG.sutunlar / yalnizVip ayarını kontrol edin.");
    /* aynı kimlik iki kez gelirse sıra numarası ekle */
    const say = {};
    liste.forEach((y) => { say[y.k] = (say[y.k] || 0) + 1; if (say[y.k] > 1) y.k += "#" + say[y.k]; });
    return liste;
  }

  /* ---------------- Koltuk haritası ---------------- */
  function renkCoz(css) {
    const m = String(css || "").match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
    if (!m || (m[4] != null && +m[4] === 0)) return null;
    return [+m[1], +m[2], +m[3]];
  }
  /* Quick Check renkleri (SeatMapHelp): lacivert = check-in/dolu, açık gri/beyaz = boş,
     koyu gri/siyah = bloke, turuncu = soft bloke, diğer renkler = dolu (ara/son bacak, transit…) */
  function durumBul(rgb) {
    if (!rgb) return "bilinmiyor";
    const [r, g, b] = rgb, L = (r + g + b) / 3, sp = Math.max(r, g, b) - Math.min(r, g, b);
    if (r > g * 1.4 && r > b * 2 && r > 110) return "bloke";          /* turuncu: soft bloke */
    if (sp < 25 && L > 185) return "bos";
    if (sp < 25 && L > 90) return "bos-son";                           /* gri: en son verilecek boş */
    if (sp < 25) return "bloke";                                       /* koyu gri / siyah */
    if (b - r > 16 && b > g + 8) return "dolu";                        /* lacivert: check-in */
    return "dolu";
  }
  function koltuklariOku() {
    const K = {};
    let n = 0;
    for (const el of document.querySelectorAll(CONFIG.koltukHucreSecici)) {
      if (el.children.length > 2) continue;
      const k = koltukNormal(hucreMetni(el));
      if (!k) continue;
      let rgb = renkCoz(getComputedStyle(el).backgroundColor);
      if (!rgb && el.parentElement) rgb = renkCoz(getComputedStyle(el.parentElement).backgroundColor);
      K[k] = durumBul(rgb);
      n++;
    }
    return n >= CONFIG.enAzKoltuk ? K : null;
  }

  /* ---------------- Farklar ---------------- */
  let onceki = null;          /* {ucus, yolcular:{k:y}, koltuklar:{}} */
  let tamGerekli = true;

  function farklar(simdi) {
    const F = [];
    if (simdi.yolcular) {
      const A = (onceki && onceki.yolcular) || {}, B = simdi.yolcular;
      for (const k of Object.keys(B)) {
        const a = A[k], b = B[k];
        if (!a) { F.push({ tip: "eklendi", k, yolcu: b }); continue; }
        if (a.koltuk !== b.koltuk) F.push({ tip: "koltuk", k, soyad: b.soyad, eski: a.koltuk, yeni: b.koltuk });
        if (a.ci !== b.ci) F.push({ tip: "checkin", k, soyad: b.soyad, eski: a.ci, yeni: b.ci });
        if (a.not !== b.not) F.push({ tip: "not", k, soyad: b.soyad, eski: a.not, yeni: b.not });
        if (a.sinif !== b.sinif) F.push({ tip: "sinif", k, soyad: b.soyad, eski: a.sinif, yeni: b.sinif });
      }
      for (const k of Object.keys(A)) if (!B[k]) F.push({ tip: "cikti", k, soyad: A[k].soyad, eski: A[k].koltuk });
    }
    if (simdi.koltuklar) {
      const A = (onceki && onceki.koltuklar) || {}, B = simdi.koltuklar;
      for (const k of Object.keys(B)) if (A[k] !== B[k]) F.push({ tip: "koltukDurum", koltuk: k, eski: A[k] || "", yeni: B[k] });
    }
    return F;
  }

  function gonder(mesaj) {
    try {
      chrome.runtime.sendMessage(mesaj, (yanit) => {
        if (chrome.runtime.lastError) return;                 /* arka plan uykudaysa sonraki turda tekrar */
        if (yanit && yanit.tamIste) tamGerekli = true;         /* arka plan durumu kaybettiyse tam görüntü iste */
      });
    } catch (e) { /* eklenti güncellendi / kaldırıldı: sessizce dur */ durdur(); }
  }

  let calisiyor = false;
  function tara() {
    if (calisiyor) return;
    calisiyor = true;
    try {
      const ucus = ucusOku();
      const liste = yolculariOku();
      const koltuklar = koltuklariOku();
      if (!liste && !koltuklar) { calisiyor = false; return; }   /* bu çerçevede okunacak bir şey yok */
      const simdi = { ucus, yolcular: null, koltuklar: koltuklar || null };
      if (liste) { simdi.yolcular = {}; liste.forEach((y) => { simdi.yolcular[y.k] = y; }); simdi.sira = liste.map((y) => y.k); }
      const ucusDegisti = onceki && ucus && onceki.ucus && (onceki.ucus.no !== ucus.no || onceki.ucus.tarih !== ucus.tarih);
      const zaman = Date.now();
      if (tamGerekli || !onceki || ucusDegisti) {
        gonder({ rita: 1, tur: "tam", ucus, yolcular: liste || null, koltuklar: koltuklar || null, zaman });
        tamGerekli = false;
        log("tam görüntü gönderildi", ucus, liste && liste.length, koltuklar && Object.keys(koltuklar).length);
      } else {
        const F = farklar(simdi);
        if (simdi.sira && onceki.sira && simdi.sira.join() !== onceki.sira.join()) F.push({ tip: "sira", sira: simdi.sira });
        gonder(F.length ? { rita: 1, tur: "fark", ucus, farklar: F, zaman } : { rita: 1, tur: "nabiz", ucus, zaman });
        if (F.length) log("farklar", F);
      }
      onceki = simdi;
    } catch (e) {
      uyar("Okuma hatası: " + (e && e.message));
    }
    calisiyor = false;
  }

  /* ---------------- Akış: aralıklı okuma + MutationObserver ---------------- */
  let zamanlayici = null, bekle = null, gozcu = null;
  function durdur() {
    clearInterval(zamanlayici); clearTimeout(bekle);
    if (gozcu) gozcu.disconnect();
  }
  zamanlayici = setInterval(tara, Math.max(500, CONFIG.taramaMs));
  gozcu = new MutationObserver(() => { clearTimeout(bekle); bekle = setTimeout(tara, CONFIG.degisimBekleMs); });
  if (document.body) gozcu.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class", "style"] });
  setTimeout(tara, 800);
  log("başladı:", yer, location.href.startsWith(CONFIG.quickCheckUrl) ? "(yolcu sayfası)" : "(iframe)");
})();
