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
- `data/ucuslar.json` — İstanbul'dan kalkan tüm THY uçuşları; `tools/canli_ucuslar.py` her 30 dakikada günceller.
- Rical listesi (`RS` in `index.html`): Başkent Protokol Listesi 1–82 (iki sayfa, kullanıcının paylaştığı), ardından THY listesinden kalan maddeler. Kullanıcı onayı olmadan sıra değiştirilmez.
- Rehber paketleri: `tools/rehber/derle.py` → `data/rehber-taslak.json`; onaylanmış `data/rehber.json` ASLA değiştirilmez; yeni kayıtlar `tools/rehber/paket_ayir.py` ile yeni paket dosyasına (`data/rehber-2.json`…) ayrılır ve `rita-veri.json` → `rehber` içinde `beklemede` belge açılır.
- `data/tbmm.json` — TBMM resmî milletvekili listesi; `tools/canli_tbmm.py` 3 saatte bir günceller. Uygulama isim aramasında kullanır (rical 21. madde, "TBMM ✓").
- `tools/resmi_gazete.py` — Resmî Gazete atama kararlarını 2 saatte bir okur (resim PDF → Türkçe OCR); teyitliler `otomatik`, teyitsizler `beklemede` olarak `degisiklikler`e eklenir.
- `site/vendor/ocr/` — cihazda çalışan Tesseract.js; check-in ekranı fotoğrafından dolu koltuk okuma.

## Planlanan (sonraki aşama)
- **Personel girişi:** THY veya TGS sicil numarası + kişinin kendi oluşturduğu şifre. Yeni kayıtlar yönetici onayıyla açılır.
  Şifresiz "Personel olarak devam et" kaldırılacak. Gerçek koruma için veriler herkese açık dosyadan çıkarılıp
  girişten sonra sunulmalı (statik sayfada istemci tarafı kontrol tek başına yeterli değil).
