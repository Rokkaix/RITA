# RITA — Rical Takip Asistanı

Protokol (rical) yolcularının resmî öncelik sırasına göre dizilmesi ve uçağın kabin düzenine göre koltuk planlaması için web uygulaması.

**Adres:** https://rokkaix.github.io/RITA/

## Özellikler
- Rical sırası: Başkent Protokol Listesi ve THY rical listesi; upgrade hakkı kontrolü (rical listesi, CIC90/95-UPGRADE)
- Koltuk planı: uçak tipine ve Quick Check koltuk haritasına göre business ve ekonomi yerleşimi
- Quick Check aktarımı: yer imi, tarayıcı eklentisi ya da ekran görüntüsü ile VIP listesi ve koltuk durumu
- Canlı uçuş listesi, görev değişikliği takibi, personel ataması ve bildirimler

## Kurulum
- **iPhone:** Safari → Paylaş → Ana Ekrana Ekle
- **Android:** Chrome → ⋮ → Uygulamayı yükle
- **Bilgisayar:** Chrome/Edge → adres çubuğundaki Yükle simgesi

## Yapı
- `index.html` — uygulama
- `site/` — manifest, service worker, RITA Canlı, yer imi sayfaları
- `data/` — ortak veriler (uçuşlar, rehber, görev değişiklikleri, kabin düzenleri)
- `eklenti/` — Quick Check okuyucu tarayıcı eklentisi
- `tools/` — veri toplayıcılar ve site derleyici
- `worker/` — bildirim sunucusu

© 2026 Yakup KAYABAŞ · Tüm hakları saklıdır.
