# RITA — Rical Takip Asistanı

## Programın amacı (her değişiklikte önce bunu düşün)
RITA'nın asıl işi **rical listesi önceliği ve koltuk ayarlamaktır**: bir uçuştaki protokol (rical) yolcularını
resmî öncelik sırasına göre dizmek ve onları uçağın kabin düzenine göre doğru koltuklara yerleştirmek.
Diğer her şey (canlı uçuş listesi, uçak tipleri, fotoğraftan dolu koltuk okuma, görev değişikliği takibi)
bu işi hızlandırmak ve doğru yapmak için vardır. Yeni özellik eklerken öncelik hep bu ana iş olmalı.

## Kullanıcı
- Sahibi ve yöneticisi: Yakup KAYABAŞ. Kod bilmiyor; açıklamalar Türkçe, sade ve adım adım olmalı.
- Görev değişiklikleri ve rehber güncellemeleri **teyit edilince otomatik işlenir** (kullanıcı kararı, 16.11.2026): Resmî Gazete metni / resmî kurum sitesi / TBMM listesi = teyitli. Teyit edilemeyen (yalnız haber, eşleşmeyen makam, "doğrulayın") ASLA işlenmez; Yönetim → Değişiklik günlüğü'nde "teyit bekliyor" olarak durur. Her işlenen değişiklik günlükte görünür, yönetici "Geri al" diyebilir.
- Rical listesinin sırası (protokol listesi) hiçbir zaman otomatik ya da kafaya göre değişmez; yalnızca kullanıcının verdiği listeye göre.
- Kabin düzeni ve sefer verisi değişiklikleri yönetici onayıyla yapılır.

## Yapı
- `index.html` — uygulamanın tamamı (tek dosya). Hem claude.ai artifact'ı hem bağımsız site bu dosyadan çıkar.
- Bağımsız site: https://rokkaix.github.io/RITA/ (GitHub Pages, `.github/workflows/rita.yml`).
- `tools/build_site.py` siteyi `_site/` içine kurar (manifest, service worker, `window.RITA_STANDALONE`).
- `data/rita-veri.json` — ortak veri (görev değişiklikleri, uçak tipi kabin düzenleri, öne çıkan hatlar).
- `data/ucuslar.json` — İstanbul'dan kalkan VE İstanbul'a gelen tüm THY uçuşları (`yon`: gidis/gelis; geliş anahtarı `TKno XXX-IST iniş`); yakın uçuşlarda canlı durum/gecikme/tahmini saat/kapı/bant. `tools/canli_ucuslar.py` her 15 dakikada (FlightStats).
- Rical listesi (`RS` in `index.html`): Başkent Protokol Listesi 1–82 (iki sayfa, kullanıcının paylaştığı), ardından THY listesinden kalan maddeler. Kullanıcı onayı olmadan sıra değiştirilmez.
- Rehber paketleri: `tools/rehber/derle.py` → `data/rehber-taslak.json`; onaylanmış `data/rehber.json` ASLA değiştirilmez; yeni kayıtlar `tools/rehber/paket_ayir.py` ile yeni paket dosyasına (`data/rehber-2.json`…) ayrılır ve `rita-veri.json` → `rehber` içinde `beklemede` belge açılır.
- `data/tbmm.json` — TBMM resmî milletvekili listesi; `tools/canli_tbmm.py` 3 saatte bir günceller. Uygulama isim aramasında kullanır (rical 21. madde, "TBMM ✓").
- `tools/resmi_gazete.py` — Resmî Gazete atama kararlarını 2 saatte bir okur (resim PDF → Türkçe OCR); teyitliler `otomatik`, teyitsizler `beklemede` olarak `degisiklikler`e eklenir.
- `data/fotolar.json` — DOĞRULANMIŞ portreler (`tools/fotolar.py`, günde bir, Actions'ta). Kaynak yalnız: TBMM resmî milletvekili sayfası ya da kişinin BUGÜNKÜ görevini (makam + il/kurum) doğrulayan Vikipedi sayfası; anlam ayrımı, ölmüş adaş, görev uyuşmazlığı → fotoğraf YOK (nedeni kayıtta). Uygulama canlı tahmin yapmaz. Fotoğraf yoksa unvana göre kurumsal avatar (`avatar()`). Yönetim → "VIP fotoğrafları": yönetici fotoğraf yükler (cihazda 360×450 kırpılır → `data/foto/*.jpg`, kayıt `rita-veri.json` → `foto`), hatalı otomatik fotoğrafı gizler (`u:'-'`). Öncelik: cihaz `D.FOTO` > ortak `foto` > `fotolar.json`. Eski görevliler de taranır; Vikipedi özetinde resim yoksa aynı sayfanın Vikidata P18 (Commons) görseli.
- Arayüz ilkesi (kurumsal, 17.11.2026): küçük/dengeli yazı, sade yüzeyler; uzun açıklamalar otomatik "Nasıl çalışır?" altında katlanır (`bilgiKatla`). Uçuş listesi "Yazdır / PDF" ile kurumsal çıktı verir (`yazdirHtml`). Ayarlar → Sistem durumu: veri tarihleri + cihazdaki hata kaydı (`rita-hata`). Örnek uçuş arayüzden kaldırıldı (17.11.2026; cihazlardaki eski örnek `D.m17` ile bir kez silinir; testlerde `A.demo()`).
- Görünüm (RITA 17, 17.11.2026): kendi kimliği — bordo (`--crim`) üst çubuk + gece mavisi (`--night`) yan menü (`cekmeceAc`, ☰), Uçuş ekranında selamlama kartı (`heroHtml`: günün VIP'li uçuşları, atama bekleyen, sıradaki uçuşa kalan süre), giriş ekranı bordo-lacivert gökyüzü. THY logosu/adı KULLANILMAZ.
- Resmî site fotoğrafları (valilik/kaymakamlık): yalnız portre (dosya adında soyadı ya da valimiz/yöneticilerimiz/özgeçmiş yolu); haber/etkinlik görseli asla.
- Bir uçuşa aynı kişi iki kez eklenemez (`zatenVar`). Yolcu satırı sade: yalnız özet etiketler; kişi/bagaj/silah/bebek/maiyet/sıra yolcu kartında. Personel ataması uçuş ekranında da (`ucAtamaHtml`); atanmış kartlar VIP listesi değişince aynı bağlantıda kendiliğinden güncellenir (`gkOtoGuncelle`). Görev kartında "‹ Geri".
- Gezinme (RITA 17.2): alt çubukta yalnız ana işler — Uçuş · Rehber · Atama · Yönetim (personelde Hesap); Rehber içinde üst alt menü Devlet · Kurumsal · CIC90 · Notlar (`REHBER`, `ALT`). Üst çubuk Uçuş dışında sayfa adını yazar. Aynı rical sırasında asıl kişi eşinden önce (`esMi`). Boş listede eylem düğmeleri gizli.
- Atama panosu (RITA 18): üstte sayaçlar (VIP'li uçuş, atama bekleyen, atandı, görevde personel); önce "ATAMA BEKLEYEN" kartlar — kart üzerinde önerilen personel (★ en az yük, saat çakışmasız; `oneriler`, `cakisma` ±60 dk) ve tek dokunuşla "Ata" (`hizliAta`); sonra "ATANMIŞ" kartlar (görevli, gönderim saati, çakışma). Personel listesinde günün uçuşları ve yük (x/6), bildirim kurulu 🔔.
- Yönetim sekmesi menülüdür (`YS`): Genel bakış, Onay bekleyenler, Görev değişiklikleri, VIP fotoğrafları, Hatlar ve uçak tipleri, Ayarlar ve güvenlik.
- `site/vendor/ocr/` — cihazda çalışan Tesseract.js; check-in ekranı fotoğrafından dolu koltuk okuma ve TROYA yolcu listesinden (PAX BY GROUP / Quick Check-in) rical eşleştirme (Modül 1).
- Koltuk kuralı: rical business/ön; eşi/refakat ricalin yanında; **maiyet ve koruma her zaman ekonomide** (bloke koltuk verilmez), yalnız "maiyet upgrade notu" varsa business'ta yer kalırsa.

## Modül 2 — Operasyon ve personel atama (sunucusuz, kullanıcı kararı 17.11.2026)
- "Atama" sekmesi yalnız yöneticide. Personel (ad, telefon) ve atamalar YALNIZ yönetici cihazında (`D.PER`, `D.GOR`, localStorage); asla `data/` ya da depoya yazılmaz.
- Görev WhatsApp'tan tek dokunuşla (`wa.me`) gider. Kısa bağlantı: VIP kartları AES-GCM ile şifrelenip `data/gorev/<id>.json`'a yazılır (yönetici GitHub anahtarıyla), bağlantı `/g/?<id>#<anahtar>` (anahtar sunucuya gitmez); 3 günden eski dosyalar silinir. Anahtar yoksa uzun `#g=` bağlantısı. `/g/` sayfası WhatsApp önizlemesi için OG etiketli.
- **Anlık bildirim + Görevlerim (kullanıcı kararı 17.11.2026):** bildirim doğrudan RITA'dan (Web Push), ek uygulama YOK. Sunucu: `worker/rita-bildirim.js` (Cloudflare Worker + KV `RITA_ABONE`; kurulum `worker/kur.py`, Cloudflare anahtarı ortam vekilinden; VAPID gizli anahtarı yalnız Worker secret'ı, depoda YOK). Her personele bir kez `kod` + `pk` (YALNIZ yönetici cihazında `D.PER`). Personel `/#p=<kod>.<pk>` sayfasını açar → RITA'yı ana ekrana ekler → "Bildirimleri aç" (abonelik koduyla `/abone`'a). Atamada yönetici `/gonder`'e (GitHub anahtarıyla doğrulanır) kısa bildirim yollar: uçuş no, VIP sayısı, şifreli kart bağlantısı; isim YOK. Görevlerim listesi şifreli `data/gorev/p-<kod>.json`. iPhone'da ana ekran uygulaması Safari'den ayrı hafıza kullanır → girişte "Görevlerimi bağla" (bağlantıyı yapıştır). `BILDIRIM_URL` index.html'de. WhatsApp yedek.
- **Canlı uçuş takibi (17.11.2026):** atanan her uçuş bildirim sunucusuna `/izle` ile kaydedilir (personel kodu + yöneticinin `D.ADMKOD`'u). Worker cron (2 dk) FlightStats'ten durum çeker (`/ucus` uç noktası da uygulamaya canlı veri verir) ve tek bildirimde birleştirerek gönderir: kapı belli oldu/değişti, saat ≥10 dk değişti, iptal, kalktı (gidiş), yaklaşıyor ≤30 dk ve inişe geçti ≤10 dk (geliş), indi + bant. KV yazımı yalnız değişince (ücretsiz kota). Atama panosunda planlanan/tahmini saat, kapı, bant, park, tescil (uçak kuyruk no, FlightStats `positional.flexTrack.tailNumber`), durum. Yönetici elle bilgi (`D.ELLE[f]`: kapı, park, not) otomatik kapının yerine geçer, görev kartında görünür, "Kaydet ve personele bildir" + kısa mesaj.
- Uygulama içi push ve gerçek rol kontrolü için sunucu gerekir (önerilen: Cloudflare ücretsiz) — kullanıcı şimdilik sunucusuzu seçti.

## Planlanan (sonraki aşama)
- **Personel girişi:** THY veya TGS sicil numarası + kişinin kendi oluşturduğu şifre. Yeni kayıtlar yönetici onayıyla açılır.
  Şifresiz "Personel olarak devam et" kaldırılacak. Gerçek koruma için veriler herkese açık dosyadan çıkarılıp
  girişten sonra sunulmalı (statik sayfada istemci tarafı kontrol tek başına yeterli değil).
