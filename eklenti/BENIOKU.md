# RITA Quick Check Okuyucu (Chrome eklentisi)

Quick Check'te açık olan uçuşun **VIP yolcu listesini** ve **koltuk haritasını** yalnızca **okur**,
RITA Canlı sayfasına (https://rokkaix.github.io/RITA/canli/) iletir. RITA Canlı yolcuları sizin
kural tablonuza göre protokol sırasına dizer ve boş koltuklara **öneri** çıkarır.

- Eklenti **giriş yapmaz, tıklamaz, yazmaz, sayfayı yenilemez**. Koltukları siz elle değiştirirsiniz.
- Giriş sayfalarında (auth.thy.com, Login.aspx) **çalışmaz**: bu adresler manifest'te yoktur, ayrıca şifre alanı
  olan bir sayfada betik kendini durdurur.
- **Hiçbir izin istemez** (permissions / host_permissions yok, `<all_urls>` yok). Yalnız iki adreste çalışır:
  `https://checkin.thy.com/V1/*` (Login.aspx hariç) ve `https://rokkaix.github.io/RITA/*`.
- Veri yalnız bellekte durur: eklenti ve RITA Canlı hiçbir şeyi diske, localStorage'a, çereze ya da sunucuya yazmaz.
  Pencere kapanınca silinir. PNR gönderilmez; addan yalnız baş harf alınır.

## Klasör yapısı

```
RITA/
├── index.html                 RITA ana uygulama
├── site/canli/index.html      RITA Canlı (eklenti verisini gösterir) → rokkaix.github.io/RITA/canli/
└── eklenti/
    ├── manifest.json          Manifest V3, izin yok
    ├── quick.js               Quick Check sayfasında OKUR (en üstte CONFIG)
    ├── arka.js                service worker: okumaları RITA sekmesine iletir
    ├── program.js             RITA sayfasında: veriyi window.postMessage ile sayfaya aktarır
    └── BENIOKU.md             bu dosya
```

Veri yolu: `quick.js` (Quick Check, her iframe) → `chrome.runtime.sendMessage` → `arka.js` →
bağlantı (port) → `program.js` → `window.postMessage` → RITA Canlı. RITA Canlı yalnız
`e.source === window`, aynı köken ve `kaynak === "eklenti"` olan, doğrulamadan geçen mesajları kabul eder.

## Ana RITA'ya otomatik aktarım

RITA ana sayfası (https://rokkaix.github.io/RITA/) açıksa eklenti verisi oraya da gider:
Quick Check'te açık uçuş RITA'nın uçuş listesinde varsa VIP'ler **rical rehberiyle** eşleştirilip uçuşa eklenir,
koltuk durumları işlenir ve yerleşim rical sırasına göre **kendiliğinden** yapılır. Uçuş ekranındaki
"CANLI · QUICK CHECK EKLENTİSİ" panelinde her otomatik işlem saatiyle yazılır; "Otomatik uygula" kapatılabilir,
"Canlı veriyi bu uçuştan kaldır" ile geri alınır. Üst düzey yolcular otomatik teyit edilmez. Canlı veri kaydedilmez.

## Sorun olursa: kendiliğinden onarım

Okuyucu bir şeyi okuyamazsa, içinde **yolcu bilgisi olmayan** kısa bir tanı raporu (uyarı, yalnız sütun başlıkları,
satır/koltuk sayısı) RITA'ya gönderir. RITA ana sayfası yönetici girişiyle açıksa bu rapor Yönetim → Asistan bölümüne
iş olarak yazılır; düzeltme `data/eklenti-ayar.json` dosyasına yazılır. Eklenti her açılışta bu dosyayı okur
(yalnız izin verilen ayar alanları, kod değil), bu yüzden **yeniden kurmanız gerekmez** — Quick Check sekmesini
yenilemeniz yeterli. Kodun kendisi değişirse bu, iş sonucunda yazılır; o zaman `chrome://extensions` → ↻.

## Kurulum (yalnız izinli bilgisayardaki Chrome)

1. Bu depodaki `eklenti` klasörünü bilgisayara indirin (GitHub → Code → Download ZIP → `eklenti` klasörünü çıkarın).
2. Chrome'da adres çubuğuna `chrome://extensions` yazın.
3. Sağ üstte **Geliştirici modu**nu açın.
4. **Paketlenmemiş öğe yükle** → `eklenti` klasörünü seçin.
5. "RITA Quick Check Okuyucu" listede görünür. Ek izin istemez.
6. Bir sekmede **RITA Canlı**'yı açın: https://rokkaix.github.io/RITA/canli/
7. Başka bir sekmede Quick Check'e kendiniz giriş yapın (şifre + 2FA) ve uçuşun **VIP Commentli Yolcu Listesi**ni açın.
8. RITA Canlı'da üstteki işaret **"Canlı · SS:DD:SS"** olur, uçuş seçilir, VIP'ler ve öneriler gelir.

Güncelleme: klasördeki dosyaları değiştirdikten sonra `chrome://extensions` → eklentinin **yenile** (↻) düğmesi,
sonra Quick Check sekmesini bir kez yenileyin.

## Demo modu (gerçek veri olmadan deneme)

1. https://rokkaix.github.io/RITA/canli/ adresini açın (eklenti gerekmez).
2. Sağ üstte **Demo modu**na basın.
3. "TK0000 / DEMO" uçuşunda DENEME1…DENEME8 adlı uydurma yolcular görünür; her 4 saniyede rastgele bir değişiklik
   (koltuk değişimi, check-in, koltuk durumu) olur ve **Değişiklik akışı**na en yeni üstte düşer.
4. **Protokol kural tablosu**nda bir önceliği değiştirin: sıralama ve öneriler hemen değişir.
5. **Koltuk planı**nda uçak tipini değiştirin ya da harf/sıra alanlarını düzenleyin.
6. **Sesli uyarı** kutusunu işaretleyip değişiklik sesini deneyin (varsayılan kapalı).
7. **Demoyu kapat**: demo verisi bellekten silinir.

## Kural tablosu

- Anahtar kelime → öncelik (küçük sayı önce). VIP notunda geçen kelimeler aranır; birden fazla eşleşirse en küçük
  öncelik geçerli. Eşleşmeyenler en sona.
- Kelime tam kelime olarak aranır, sonuna en çok 2 harf ek gelebilir: "BAKAN" → "BAKANI" tutar, "BAKANLIGI" tutmaz.
- **Business** kutusu işaretli kurallara business koltuk önerilir; diğerlerine (maiyet, görevli, kuralı olmayan)
  yalnız ekonomi.
- Varsayılan satırlar örnektir (gerçek isim yok). Quick Check notlarında yazım farkları olabilir
  (ör. "BASKAN VEKILLI"); gerekirse o yazımı da ayrı kural olarak ekleyin. "TBMM BASKANI" gibi üst makamları
  kendi önceliğinizle ekleyin.
- Sayfa hiçbir şeyi saklamadığı için kuralları "Kuralları sakla / geri yükle" bölümünden metin olarak alıp
  kendi bilgisayarınızda saklayın; sonraki açılışta yapıştırıp "Yükle"ye basın.

## CONFIG'i gerçek sayfaya uyarlama

Varsayılan ayar, tablo satırlarını **başlık satırındaki yazılara** bakarak okur ("Klt", "S", "Soyad", "Ad", "C"…),
koltuk haritasında ise yazısı koltuk koduna benzeyen (01A, 12C…) hücreleri bulup **arka plan rengini** okur.
Çoğu durumda değişiklik gerekmez. Okumazsa:

1. Quick Check'te uçuşu açın, **F12** ile Geliştirici Araçları'nı açın, **Console** sekmesine geçin.
   Okuyucunun uyarıları `[RITA okuyucu]` ile başlar (ör. "Yolcu listesi başlığı bulundu ama VIP satır okunamadı").
2. Ayrıntı için `quick.js` en üstündeki `CONFIG` içinde `hataAyikla: true` yapın, eklentiyi yenileyin; Console'da her
   okumanın özeti görünür.
3. **Seçici bulma:** listede bir yolcu satırına sağ tıklayın → **İncele**. Elements panelinde satırın `<tr>` öğesi
   seçilir. Liste bir iframe içindeyse Console'un üstündeki açılır menüden (top ▾) o iframe'i seçebilirsiniz.
   - Satır `<tr>` ise `satirSecici: "tr"` yeterlidir. Satırların özel bir sınıfı/kimliği varsa daraltın,
     ör. `satirSecici: "#gvYolcu tr"` ya da `"table.yolcuListesi tr"`.
   - Seçiciyi Console'da deneyin: `document.querySelectorAll("SEÇİCİ").length` → satır sayısını vermeli.
4. **Sütun sırası:** başlık satırı okunamıyorsa `otomatikBaslik: false` yapın ve `sutunlar` içindeki sayıları,
   satırdaki hücre sırasına göre (0'dan başlayarak) yazın. Console'da kontrol:
   `[...document.querySelectorAll("SEÇİCİ")[5].children].map((td,i)=>i+": "+td.textContent.trim())`
5. **Check-in sütunu:** hücrede resim/simge ya da `checkinIsaretleri` içindeki işaretlerden biri varsa "yapıldı"
   sayılır. Check-in olmayan satırlarda da farklı bir simge varsa, simgenin `src`/`class` adına göre
   `checkinMi` işlevindeki seçiciyi daraltın.
6. **Koltuk haritası:** koltuk kutusuna sağ tıklayın → İncele. Kutular `<td>` değilse (ör. `<div class="seat">`)
   `koltukHucreSecici: "div.seat"` yazın. Renk kutunun kendi arka planından (yoksa üst öğesinden) okunur.
7. **Uçuş başlığı:** "Uçuş: TK2150 / 22NOV" yazısı okunamıyorsa başlığın öğesini `ucusBaslikSecici` ile verin.
8. Her değişiklikten sonra `chrome://extensions` → ↻ → Quick Check sekmesini yenileyin.

## Sınırlar

- Koltuk durumu renkten çıkarılır: lacivert/diğer renkler = dolu, açık gri = boş, orta gri = boş (en son verilecek),
  koyu gri/siyah/turuncu = bloke. Bebek, tekerlekli sandalye gibi simgeler okunmaz.
- Liste kaydırılarak sonradan yüklenen satırlar, sayfaya eklendikleri anda (MutationObserver) okunur; ekranda hiç
  yüklenmemiş satırlar okunamaz.
- Chrome servis çalışanı uykuya geçip uyanabilir; bu durumda okuyucu bir sonraki turda tam görüntüyü yeniden gönderir.
