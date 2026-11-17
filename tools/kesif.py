"""Keşif: verilen sayfaları indirip yapısını günlüğe yazar (resimler, başlıklar, bağlantılar, olası JSON uç noktaları). Veri yazmaz."""
import sys, re, html, subprocess
def get(u):
    return subprocess.run(['curl', '-sL', '-m', '40', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36', '-w', '\n@@KOD %{http_code} %{url_effective}', u], capture_output=True).stdout.decode('utf-8', 'ignore')
for u in sys.argv[1:]:
    h = get(u); kod = h.rsplit('@@KOD', 1)[-1].strip(); h = h.rsplit('@@KOD', 1)[0]
    print('=' * 100); print('ADRES', u, '→', kod, len(h), 'bayt')
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S | re.I)
    print('BAŞLIKLAR:', [re.sub(r'<[^>]+>', '', x).strip()[:80] for x in re.findall(r'<h[1-4][^>]*>.*?</h[1-4]>', t, re.S | re.I)][:60])
    for im in re.findall(r'<img\b[^>]*>', h, re.I)[:80]: print('IMG', im[:260])
    for m in sorted(set(re.findall(r'["\'](/[^"\']*(?:api|json|yonetim|management|board|kurul)[^"\']*)["\']', h, re.I)))[:40]: print('YOL', m[:200])
    for m in sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h, re.I))):
        if re.search(r'(?i)yonetim|management|board|kurul|hakkimizda|about|rektor|baskan|bakan', m): print('LINK', m[:200])
    duz = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))
    print('METİN:', duz[:6000])
