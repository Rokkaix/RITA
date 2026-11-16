# RITA — Rical Takip Asistanı

THY seferleri için rical sırası, upgrade ve koltuk yönetimi.

**Uygulama adresi:** https://rokkaix.github.io/RITA/

## Telefona / bilgisayara yükleme
- **iPhone:** Safari'de adresi açın → Paylaş → **Ana Ekrana Ekle**
- **Android:** Chrome'da açın → çıkan **Yükle** düğmesi (ya da ⋮ → Uygulamayı yükle)
- **Bilgisayar:** Chrome/Edge'de açın → adres çubuğundaki **Yükle** simgesi

## Nasıl güncellenir
- **Her gün 05:43:** GitHub, takip edilen hatlardaki THY seferlerini (Yönetim → Takip edilen hatlar) ve uçak tiplerini toplar (`tools/gunluk_seferler.py`) ve `data/rita-veri.json` dosyasına **onay bekleyen** kayıt olarak yazar.
- **Her pazartesi:** Resmî Gazete görev değişiklikleri onay bekleyen kayıt olarak eklenir.
- Yönetici uygulamada **Yönetim** sekmesinden onaylar. Onaylanmadan hiçbir şey değişmez.
- Her değişiklikte site kendiliğinden yeniden yayınlanır (`.github/workflows/rita.yml`).

## Dosyalar
- `index.html` — uygulama
- `data/rita-veri.json` — ortak veriler (seferler, görev değişiklikleri, uçak tipi kabin düzenleri)
- `site/` — simgeler, manifest, çevrimdışı çalışma (service worker), yükleme uyarısı
- `tools/` — sefer toplayıcı ve site kurucu

© 2026 Yakup KAYABAŞ · Tüm hakları saklıdır.
