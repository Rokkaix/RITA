"""RITA'nın bağımsız sitesini _site/ klasörüne kurar (GitHub Pages bunu yayınlar)."""
import os, shutil, hashlib, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, "_site")
shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(os.path.join(R, "site"), OUT)
shutil.copytree(os.path.join(R, "data"), os.path.join(OUT, "data"))
html = open(os.path.join(R, "index.html"), encoding="utf-8").read()
ver = hashlib.sha1(html.encode()).hexdigest()[:10]
head = (
    '<link rel="manifest" href="manifest.webmanifest">'
    '<meta name="theme-color" content="#7f0f22">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
    '<meta name="apple-mobile-web-app-title" content="RITA">'
    '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">'
    '<link rel="icon" type="image/svg+xml" href="icons/rita.svg">'
    '<meta name="robots" content="noindex">'
    '<meta property="og:site_name" content="RITA">'
    '<meta property="og:title" content="RITA · Rical Takip Asistanı">'
    '<meta property="og:description" content="Rical listesi önceliği ve koltuk yerleşimi">'
    '<meta property="og:image" content="https://rokkaix.github.io/RITA/icons/icon-512.png">'
    '<meta property="og:type" content="website">'
    '<script>window.RITA_STANDALONE=1</script>'
)
html = html.replace("</head>", head + "</head>", 1)
tail = open(os.path.join(R, "site", "kurulum.html"), encoding="utf-8").read()
html = html.replace("</body>", tail + "</body>", 1)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
os.remove(os.path.join(OUT, "kurulum.html"))
sw = os.path.join(OUT, "sw.js")
open(sw, "w").write(open(sw).read().replace("__SURUM__", ver))
open(os.path.join(OUT, ".nojekyll"), "w").close()
# kısa görev bağlantısı: /g/?<kimlik>#<anahtar> -> WhatsApp önizlemesinde sade bir RITA kartı, açılınca uygulamaya yönlenir
os.makedirs(os.path.join(OUT, "g"), exist_ok=True)
open(os.path.join(OUT, "g", "index.html"), "w", encoding="utf-8").write('''<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RITA · Görev kartı</title>
<meta name="robots" content="noindex">
<meta property="og:site_name" content="RITA"><meta property="og:title" content="RITA · Görev kartı">
<meta property="og:description" content="Size atanan uçuşun VIP yolcu kartları. Açmak için dokunun.">
<meta property="og:image" content="https://rokkaix.github.io/RITA/icons/icon-512.png"><meta property="og:image:width" content="512"><meta property="og:image:height" content="512">
<meta property="og:type" content="website"><meta name="twitter:card" content="summary">
<link rel="icon" href="../icons/rita.svg"><meta name="theme-color" content="#7f0f22">
<style>body{margin:0;font:16px system-ui;background:#1d3461;color:#fff;display:flex;min-height:100vh;align-items:center;justify-content:center}</style></head>
<body><p>Görev kartları açılıyor…</p><script>var id=location.search.slice(1).split('&')[0],k=location.hash.slice(1);location.replace('../#gk='+id+'.'+k)</script></body></html>''')
print("site hazır:", OUT, "sürüm", ver)
