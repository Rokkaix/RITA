"""İçişleri Bakanlığı valilikler sayfası (icisleri.gov.tr/valilikler) -> 81 vali JSON."""
import sys, re, json, html, subprocess, os
sys.path.insert(0, os.path.dirname(__file__))
from tbmm import name_fix
s = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv) > 1 else subprocess.run(['curl', '-s', '-m', '60', '-A', 'Mozilla/5.0', 'https://www.icisleri.gov.tr/valilikler'], capture_output=True, text=True).stdout
out = []
for m in re.finditer(r'<h3 class="cityname">([^<]+)</h3>\s*<span class="d-none vali">([^<]*)</span>', s):
    out.append({'il': html.unescape(m.group(1)).strip(), 'n': name_fix(html.unescape(m.group(2)).strip())})
print(json.dumps(out, ensure_ascii=False, indent=0))
