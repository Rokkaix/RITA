/* RITA yer imi (bookmarklet): Quick Check sayfasında tıklanınca VIP listesini ve koltuk haritasını YALNIZ OKUR,
   RITA sekmesine gönderir. Hiçbir şey yazmaz, tıklamaz. Giriş/şifre sayfalarında çalışmaz.
   tools/build_site.py bu dosyayı tek satıra indirip site/yerimi sayfasına "javascript:" bağlantısı olarak koyar.
   Kurallar: yalnız blok yorum, her deyim noktalı virgülle biter (tek satıra indirilebilsin). */
(function () {
  var SURUM = 8, RITA = "https://rokkaix.github.io", ADRES = RITA + "/RITA/#qc";
  var demo = location.origin === RITA && /\/RITA\/yerimi\/deneme/.test(location.pathname);
  if (location.hostname !== "checkin.thy.com" && !demo) { alert("RITA: Bu düğme yalnız Quick Check sayfasında çalışır."); return; }
  if (/Login\.aspx/i.test(location.href) || document.querySelector("input[type=password]")) { alert("RITA: Giriş sayfasında çalışmaz. Önce uçuşu açın."); return; }
  var sade = function (t) { return String(t || "").replace(/\s+/g, " ").trim().replace(/[iı]/g, function (c) { return c === "i" ? "İ" : "I"; }).toUpperCase().replace(/İ/g, "I").replace(/Ş/g, "S").replace(/Ğ/g, "G").replace(/Ü/g, "U").replace(/Ö/g, "O").replace(/Ç/g, "C"); };
  var metin = function (e) { return e ? String(e.textContent || "").replace(/\s+/g, " ").trim() : ""; };
  var kol = function (t) { var m = String(t || "").toUpperCase().match(/^\s*0?(\d{1,2})([A-K])\s*$/); return m ? String(parseInt(m[1], 10)) + m[2] : ""; };
  var BAS = { klt: ["klt", "koltuk"], cl: ["cl", "ci"], s: ["s"], soyad: ["soyad", "yolcu soyadi"], ad: ["ad"], c: ["c", "comment", "aciklama"], gk: ["gk"] };
  /* Quick Check'te okunacak belgeler: sayfa + aynı kökenli iframe'ler (her taramada yeniden toplanır) */
  var belgeTopla = function () { var L = []; (function topla(w, d) { try { var b = w.document; if (!b || d > 4) return; L.push(b); for (var i = 0; i < w.frames.length; i++) topla(w.frames[i], d + 1); } catch (e) {} })(window, 0); return L; };
  /* Sayfa numarası (VIP listesi birden çok sayfa olabilir): ASP.NET sayfalayıcı bağlantıları "Page$2"; o anki sayfa bağlantısız (span) yazılır. */
  var sayfaBul = function (b) {
    var pl = b.querySelectorAll('a[href*="Page$"]'); if (!pl.length) return { sayfa: 0, toplam: 0 };
    var nums = [], daha = 0; Array.prototype.forEach.call(pl, function (a) { var t = metin(a); if (/^\d{1,2}$/.test(t)) nums.push(+t); else if (/^\.\.\.$|^>|^»/.test(t)) daha = 1; });
    var kap = pl[0].closest("table") || pl[0].parentElement, cur = 0;
    Array.prototype.forEach.call(kap.querySelectorAll("span,b,strong,td"), function (s) { if (!cur && !s.querySelector("a") && !s.closest("a") && s.children.length === 0 && /^\s*\d{1,2}\s*$/.test(s.textContent)) cur = +metin(s); });
    if (!cur) return { sayfa: 0, toplam: 0 };
    return { sayfa: cur, toplam: daha ? 0 : Math.max.apply(null, nums.concat([cur])) };
  };
  /* Tek tarama: YALNIZ OKUR (hiçbir şeye tıklamaz, yazmaz) */
  var tara = function () {
    var ucus = null, yolcular = null, koltuklar = null, kn = 0, sy = { sayfa: 0, toplam: 0 };
    belgeTopla().forEach(function (b) {
      var gm = String((b.body && (b.body.innerText || b.body.textContent)) || "").match(/U[çc]u[şs]\s*:\s*(TK\s?\d{2,5})\s*\/\s*(\d{1,2}[A-ZĞÜŞİÖÇ]{3})/i);
      if (gm && !ucus) { ucus = { no: "TK" + String(parseInt(gm[1].replace(/\D/g, ""), 10)), tarih: gm[2].toUpperCase() }; var kp = String((b.body && (b.body.innerText || b.body.textContent)) || "").match(/Kap[ıi]\s*:\s*([A-Z0-9]{1,6})\b/i); if (kp) ucus.kapi = kp[1].toUpperCase(); }
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
          /* Quick Check satır numarası (1–10, 11–20…): sayfalar arası sıra ve sayfa ayrımı için; sayfa numarası okunamasa da çalışır */
          for (var q = 0; q < Math.min(3, td.length); q++) { var sn2 = metin(td[q]); if (/^\d{1,3}$/.test(sn2)) { y.no = +sn2; break; } }
          y.k = [y.soyad, y.adBas, gk].join("|"); say[y.k] = (say[y.k] || 0) + 1; if (say[y.k] > 1) y.k += "#" + say[y.k];
          L.push(y);
        });
        yolcular = L; sy = sayfaBul(b);
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
    if (!yolcular && !koltuklar) return null;
    /* "Toplam 6 C 19 Y Yolcu" ya da "Toplam 3 Y Yolcu" → listede beklenen VIP sayısı */
    var bek = 0; belgeTopla().forEach(function (b) { var tx = String((b.body && b.body.innerText) || ""), t = tx.match(/Toplam\s*(\d{1,3})\s*C\s*(\d{1,3})\s*Y/i), t2 = tx.match(/Toplam\s*(\d{1,3})\s*[CY]\s*Yolcu/i); if (!bek && t) bek = +t[1] + +t[2]; else if (!bek && t2) bek = +t2[1]; });
    /* Birikim: Quick Check sayfa değiştirirken kendini yenilese de önceki sayfalar kaybolmasın diye, bu sekmede görülen satırlar
       sekmenin kendi belleğinde (window.name) tutulur ve her gönderimde HEPSİ gider. Diske yazılmaz; sekme kapanınca silinir.
       Başka bir uçuşa geçilince ya da 3 saat sonra sıfırlanır. window.name başka bir amaçla doluysa kullanılmaz. */
    if (yolcular && ucus && yolcular.length && yolcular.every(function (y) { return y.no; })) {
      var BK = "__rita_qc:", o = null, wn = String(window.name || "");
      if (!wn || wn.indexOf(BK) === 0) {
        try { o = wn ? JSON.parse(wn.slice(BK.length)) : null; } catch (e) { o = null; }
        var uk = ucus.no + "/" + ucus.tarih;
        if (!o || o.u !== uk || Date.now() - (o.t || 0) > 3 * 3600 * 1000) o = { u: uk, t: Date.now(), r: {} };
        var yeniK = {}; yolcular.forEach(function (y) { yeniK[y.k] = y.no; });
        Object.keys(o.r).forEach(function (n) { var e = o.r[n]; if (yeniK[e.k] != null && yeniK[e.k] !== e.no) delete o.r[n]; });
        yolcular.forEach(function (y) { o.r[y.no] = y; });
        if (bek) Object.keys(o.r).forEach(function (n) { if (+n > bek) delete o.r[n]; });
        o.t = Date.now();
        try { window.name = BK + JSON.stringify(o); } catch (e) {}
        yolcular = Object.keys(o.r).map(function (n) { return o.r[n]; }).sort(function (a, b) { return a.no - b.no; }).slice(0, 400);
      }
    }
    var ilkNo = 0; if (yolcular) yolcular.forEach(function (y) { if (y.no && (!ilkNo || y.no < ilkNo)) ilkNo = y.no; });
    var msg = { kaynak: "yerimi", surum: SURUM, tur: "tam", demo: demo ? 1 : 0, ucus: ucus, yolcular: yolcular, koltuklar: koltuklar, sayfa: sy.sayfa, toplam: sy.toplam, ilkNo: ilkNo, beklenen: bek, zaman: Date.now() };
    var ozet = (ucus ? ucus.no + ": " : "") + (yolcular ? yolcular.length + " VIP" + (sy.sayfa ? " (sayfa " + sy.sayfa + (sy.toplam ? "/" + sy.toplam : "") + ")" : "") : "liste yok") + ", " + (koltuklar ? kn + " koltuk" : "koltuk haritası yok");
    return { msg: msg, ozet: ozet };
  };
  /* Zaten takipteyse (yer imine ikinci kez dokunuldu): hemen tara, gönder, RITA'yı öne getirme */
  var T = window.__ritaTakip;
  if (T && T.w && !T.w.closed) { T.simdi(); return; }
  var ilk = tara();
  if (!ilk) { alert("RITA: Bu sayfada VIP yolcu listesi ya da koltuk haritası bulunamadı. Uçuşun VIP Commentli Yolcu Listesi açıkken deneyin."); return; }
  var msg = ilk.msg, ozet = ilk.ozet;
  /* TAKİP: siz Quick Check'te sayfa 2/3'e geçtikçe ya da liste/koltuklar değiştikçe değişen kısım kendiliğinden RITA'ya gider.
     Hiçbir şeye tıklanmaz; yalnız sayfa değişimi izlenir (MutationObserver). Saat gibi küçük değişiklikler yok sayılır,
     taramalar en az 1,5 sn arayla ve yalnız sayfa sakinleşince (0,7 sn) yapılır; aynı veri tekrar gönderilmez → Quick Check yavaşlamaz. */
  var takipBaslat = function (w, imza0) {
    var son = imza0, zam = null, sonT = 0, bas = Date.now(), izlenen = [], dokunus = 0;
    var gonder = function () {
      zam = null;
      if (w.closed || Date.now() - bas > 6 * 3600 * 1000) { dur(); return; }
      var r = tara(); if (!r) return;
      var imza = JSON.stringify([r.msg.ucus, r.msg.sayfa, r.msg.yolcular, r.msg.koltuklar]); if (imza === son) return;
      son = imza; if (dokunus) dokunus = 0; else r.msg.takip = 1; sonT = Date.now();
      try { w.postMessage(r.msg, RITA); } catch (e) {}
    };
    var planla = function () { if (zam) return; zam = setTimeout(gonder, Math.max(700, 1500 - (Date.now() - sonT))); };
    var kucuk = function (m) { var t = m.target; var e = t && t.nodeType === 3 ? t.parentNode : t; return !!e && String(e.textContent || "").length < 30; };
    var gozcu = function (L) { if (L.every(kucuk)) return; planla(); };
    var bagla = function () { belgeTopla().forEach(function (b) { if (izlenen.indexOf(b) >= 0 || !b.body) return; izlenen.push(b); try { var o = new b.defaultView.MutationObserver(gozcu); o.observe(b.body, { childList: true, subtree: true, characterData: true }); izlenen.push(o); } catch (e) {} }); };
    var aralik = setInterval(function () { if (w.closed) { dur(); return; } izlenen = izlenen.filter(function (x) { return !(x && x.defaultView === null); }); bagla(); }, 3000);
    var dur = function () { clearInterval(aralik); clearTimeout(zam); izlenen.forEach(function (x) { if (x && x.disconnect) x.disconnect(); }); izlenen = []; window.__ritaTakip = null; };
    /* NABIZ: takip açıkken 15 sn'de bir RITA'ya "canlıyım" sinyali (yalnız uçuş no, yolcu bilgisi yok); sayfa kapanır ya da yenilenirse "kapandı" haberi.
       RITA böylece takibin açık olup olmadığını gösterir; durduysa yer imine bir kez dokunmanız gerektiğini söyler. */
    var nabizNo = function () { var r = tara(); return r && r.msg.ucus ? r.msg.ucus.no : (msg.ucus ? msg.ucus.no : ""); };
    var nabiz = setInterval(function () { if (w.closed) { dur(); return; } try { w.postMessage({ kaynak: "yerimi", surum: SURUM, tur: "nabiz", demo: demo ? 1 : 0, ucus: { no: nabizNo() } }, RITA); } catch (e) {} }, 15000);
    var kapan = function () { try { if (!w.closed) w.postMessage({ kaynak: "yerimi", surum: SURUM, tur: "kapandi", demo: demo ? 1 : 0, ucus: { no: msg.ucus ? msg.ucus.no : "" } }, RITA); } catch (e) {} };
    window.addEventListener("pagehide", kapan);
    var dur0 = dur; dur = function () { clearInterval(nabiz); window.removeEventListener("pagehide", kapan); dur0(); };
    bagla();
    window.__ritaTakip = { w: w, simdi: function () { son = ""; clearTimeout(zam); dokunus = 1; gonder(); }, dur: dur };
  };
  var w = null; try { w = window.open(ADRES, "rita_qc"); } catch (e) {}
  var tamam = 0, n2 = 0;
  var yedek = function () {
    var t = JSON.stringify(msg);
    var bitti = function () { alert("RITA: " + ozet + " okundu ve kopyalandı.\nRITA'yı açın, uçuş ekranında \"Quick Check'ten yapıştır\" düğmesine basın (bilgisayarda Ctrl+V da olur).\nSayfa 2/3 varsa o sayfaya geçip yer imine tekrar dokunun."); };
    try { navigator.clipboard.writeText(t).then(bitti, function () { prompt("RITA: Aşağıdaki metni kopyalayıp RITA'da yapıştırın:", t); }); } catch (e) { prompt("RITA: Aşağıdaki metni kopyalayıp RITA'da yapıştırın:", t); }
  };
  if (!w || w.closed) { yedek(); return; }
  var dinle = function (e) { if (e.origin === RITA && e.data && e.data.kaynak === "rita" && e.data.tur === "alindi") { tamam = 1; window.removeEventListener("message", dinle); takipBaslat(w, JSON.stringify([msg.ucus, msg.sayfa, msg.yolcular, msg.koltuklar])); } };
  window.addEventListener("message", dinle);
  var z = setInterval(function () {
    if (tamam) { clearInterval(z); return; }
    if (++n2 > 24 || w.closed) { clearInterval(z); window.removeEventListener("message", dinle); yedek(); return; }
    try { w.postMessage(msg, RITA); } catch (e) {}
  }, 500);
})();
