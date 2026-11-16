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
    '<meta name="theme-color" content="#1d3461">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
    '<meta name="apple-mobile-web-app-title" content="RITA">'
    '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">'
    '<link rel="icon" type="image/svg+xml" href="icons/rita.svg">'
    '<meta name="robots" content="noindex">'
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
print("site hazır:", OUT, "sürüm", ver)
