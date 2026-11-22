/* RITA yer imi (bookmarklet): Quick Check sayfasında tıklanınca VIP listesini ve koltuk haritasını YALNIZ OKUR,
   RITA sekmesine gönderir. Hiçbir şey yazmaz, tıklamaz. Giriş/şifre sayfalarında çalışmaz.
   tools/build_site.py bu dosyayı tek satıra indirip site/yerimi sayfasına "javascript:" bağlantısı olarak koyar.
   Kurallar: yalnız blok yorum, her deyim noktalı virgülle biter (tek satıra indirilebilsin). */
(function () {
  var SURUM = 1, RITA = "https://rokkaix.github.io", ADRES = RITA + "/RITA/#qc";
  var demo = location.origin === RITA && /\/RITA\/yerimi\/deneme/.test(location.pathname);
  if (location.hostname !== "checkin.thy.com" && !demo) { alert("RITA: Bu düğme yalnız Quick Check sayfasında çalışır."); return; }
  if (/Login\.aspx/i.test(location.href) || document.querySelector("input[type=password]")) { alert("RITA: Giriş sayfasında çalışmaz. Önce uçuşu açın."); return; }
  var sade = function (t) { return String(t || "").replace(/\s+/g, " ").trim().replace(/[iı]/g, function (c) { return c === "i" ? "İ" : "I"; }).toUpperCase().replace(/İ/g, "I").replace(/Ş/g, "S").replace(/Ğ/g, "G").replace(/Ü/g, "U").replace(/Ö/g, "O").replace(/Ç/g, "C"); };
  var metin = function (e) { return e ? String(e.textContent || "").replace(/\s+/g, " ").trim() : ""; };
  var kol = function (t) { var m = String(t || "").toUpperCase().match(/^\s*0?(\d{1,2})([A-K])\s*$/); return m ? String(parseInt(m[1], 10)) + m[2] : ""; };
  var BAS = { klt: ["klt", "koltuk"], cl: ["cl", "ci"], s: ["s"], soyad: ["soyad", "yolcu soyadi"], ad: ["ad"], c: ["c", "comment", "aciklama"], gk: ["gk"] };
  var belgeler = [];
  (function topla(w, d) { try { var b = w.document; if (!b || d > 4) return; belgeler.push(b); for (var i = 0; i < w.frames.length; i++) topla(w.frames[i], d + 1); } catch (e) {} })(window, 0);
  var ucus = null, yolcular = null, koltuklar = null, kn = 0;
  belgeler.forEach(function (b) {
    var gm = String((b.body && (b.body.innerText || b.body.textContent)) || "").match(/U[çc]u[şs]\s*:\s*(TK\s?\d{2,5})\s*\/\s*(\d{1,2}[A-ZĞÜŞİÖÇ]{3})/i);
    if (gm && !ucus) ucus = { no: gm[1].replace(/\s+/g, "").toUpperCase(), tarih: gm[2].toUpperCase() };
    var S = Array.prototype.slice.call(b.querySelectorAll("tr")), h = null, bi = -1, liste = null;
    for (var i = 0; i < S.length && !h; i++) {
      var H = Array.prototype.map.call(S[i].children, function (x) { return sade(metin(x)).toLowerCase(); });
      if (!H.some(function (x) { return BAS.soyad.indexOf(x) >= 0; })) continue;
      var m = {}; Object.keys(BAS).forEach(function (k) { var j = H.findIndex(function (x) { return BAS[k].indexOf(x) >= 0; }); if (j >= 0) m[k] = j; });
      if (m.soyad != null && m.klt != null) { h = m; bi = i; liste = S[i].closest("table"); }
    }
    if (h && !yolcular) {
      var L = [], say = {};
      S.slice(bi + 1).forEach(function (tr) {
        var td = tr.children; if (td.length < 6) return;
        var soyad = metin(td[h.soyad]).replace(/[^A-Za-zÇĞİÖŞÜçğıöşü' -]/g, "").trim(); if (!soyad) return;
        var not = h.c != null ? metin(td[h.c]) : ""; if (sade(not).indexOf("!VIP!") < 0) return;
        var ad = h.ad != null ? metin(td[h.ad]) : "", sn = h.s != null ? metin(td[h.s]).toUpperCase().slice(0, 1) : "", gk = h.gk != null ? metin(td[h.gk]).slice(0, 6) : "";
        var c = h.cl != null ? td[h.cl] : null, ci = !!c && (!!c.querySelector("img,svg,i") || /✔|✓|√|\bOK\b|^Y$/i.test(metin(c)));
        var y = { soyad: soyad.toUpperCase().slice(0, 40), adBas: ad ? ad.charAt(0).toUpperCase() : "", koltuk: kol(metin(td[h.klt])), ci: ci, sinif: /^[A-Z]$/.test(sn) ? sn : "", not: not.slice(0, 300) };
        y.k = [y.soyad, y.adBas, gk].join("|"); say[y.k] = (say[y.k] || 0) + 1; if (say[y.k] > 1) y.k += "#" + say[y.k];
        L.push(y);
      });
      yolcular = L;
    }
    var K = {}, n = 0, gw = b.defaultView;
    Array.prototype.forEach.call(b.querySelectorAll("td,div.seat"), function (el) {
      if (el.children.length > 2 || (liste && liste.contains(el))) return; var k = kol(metin(el)); if (!k) return;
      var rgb = null, e = el;
      for (var u = 0; u < 2 && e && !rgb; u++, e = e.parentElement) { var r = String(gw.getComputedStyle(e).backgroundColor).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/); if (r && !(r[4] != null && +r[4] === 0)) rgb = [+r[1], +r[2], +r[3]]; }
      var d = "bilinmiyor";
      if (rgb) { var R = rgb[0], G = rgb[1], B = rgb[2], Lm = (R + G + B) / 3, sp = Math.max(R, G, B) - Math.min(R, G, B);
        d = R > G * 1.4 && R > B * 2 && R > 110 ? "soft" : sp < 25 && Lm > 185 ? "bos" : sp < 25 && Lm > 90 ? "bos-son" : sp < 25 ? "bloke" : "dolu"; }
      K[k] = d; n++;
    });
    if (n >= 12 && n > kn) { koltuklar = K; kn = n; }
  });
  if (!yolcular && !koltuklar) { alert("RITA: Bu sayfada VIP yolcu listesi ya da koltuk haritası bulunamadı. Uçuşun VIP Commentli Yolcu Listesi açıkken deneyin."); return; }
  var msg = { kaynak: "yerimi", surum: SURUM, tur: "tam", demo: demo ? 1 : 0, ucus: ucus, yolcular: yolcular, koltuklar: koltuklar, zaman: Date.now() };
  var ozet = (ucus ? ucus.no + ": " : "") + (yolcular ? yolcular.length + " VIP" : "liste yok") + ", " + (koltuklar ? kn + " koltuk" : "koltuk haritası yok");
  var w = null; try { w = window.open(ADRES, "rita_qc"); } catch (e) {}
  var tamam = 0, n2 = 0;
  var yedek = function () {
    var t = JSON.stringify(msg);
    var bitti = function () { alert("RITA: " + ozet + " okundu ve kopyalandı.\nRITA'yı açın, uçuş ekranında \"Quick Check'ten yapıştır\" düğmesine basın (bilgisayarda Ctrl+V da olur)."); };
    try { navigator.clipboard.writeText(t).then(bitti, function () { prompt("RITA: Aşağıdaki metni kopyalayıp RITA'da yapıştırın:", t); }); } catch (e) { prompt("RITA: Aşağıdaki metni kopyalayıp RITA'da yapıştırın:", t); }
  };
  if (!w || w.closed) { yedek(); return; }
  var dinle = function (e) { if (e.origin === RITA && e.data && e.data.kaynak === "rita" && e.data.tur === "alindi") { tamam = 1; window.removeEventListener("message", dinle); } };
  window.addEventListener("message", dinle);
  var z = setInterval(function () {
    if (tamam) { clearInterval(z); return; }
    if (++n2 > 24 || w.closed) { clearInterval(z); window.removeEventListener("message", dinle); yedek(); return; }
    try { w.postMessage(msg, RITA); } catch (e) {}
  }, 500);
})();
