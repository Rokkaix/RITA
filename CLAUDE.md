# RITA — Rical Takip Asistanı

## Programın amacı (her değişiklikte önce bunu düşün)
RITA'nın asıl işi **rical listesi önceliği ve koltuk ayarlamaktır**: bir uçuştaki protokol (rical) yolcularını
resmî öncelik sırasına göre dizmek ve onları uçağın kabin düzenine göre doğru koltuklara yerleştirmek.
Diğer her şey (canlı uçuş listesi, uçak tipleri, fotoğraftan dolu koltuk okuma, görev değişikliği takibi)
bu işi hızlandırmak ve doğru yapmak için vardır. Yeni özellik eklerken öncelik hep bu ana iş olmalı.

## Kullanıcı
- Sahibi ve yöneticisi: Yakup KAYABAŞ. Kod bilmiyor; açıklamalar Türkçe, sade ve adım adım olmalı.
- Her ortak değişiklik (atama, sefer verisi, kabin düzeni) yönetici onayıyla yapılır.

## Yapı
- `index.html` — uygulamanın tamamı (tek dosya). Hem claude.ai artifact'ı hem bağımsız site bu dosyadan çıkar.
- Bağımsız site: https://rokkaix.github.io/RITA/ (GitHub Pages, `.github/workflows/rita.yml`).
- `tools/build_site.py` siteyi `_site/` içine kurar (manifest, service worker, `window.RITA_STANDALONE`).
- `data/rita-veri.json` — ortak veri (görev değişiklikleri, uçak tipi kabin düzenleri, öne çıkan hatlar).
- `data/ucuslar.json` — İstanbul'dan kalkan tüm THY uçuşları; `tools/canli_ucuslar.py` her 30 dakikada günceller.
- `site/vendor/ocr/` — cihazda çalışan Tesseract.js; check-in ekranı fotoğrafından dolu koltuk okuma.
