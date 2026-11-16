"""Cumhurbaşkanlığı Kabinesi (tccb.gov.tr/kabine) -> JSON."""
import sys, re, json, html, subprocess
sys.path.insert(0, __import__('os').path.dirname(__file__))
from tbmm import name_fix
s = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv) > 1 else subprocess.run(['curl', '-s', '-m', '60', '-A', 'Mozilla/5.0', 'https://www.tccb.gov.tr/kabine/'], capture_output=True, text=True).stdout
out = []
for m in re.finditer(r'<p class="president-title"><a[^>]*>([^<]+)</a></p><p class="president-time-line">(.*?)</p>', s, re.S):
    out.append({'n': name_fix(html.unescape(m.group(1)).strip()), 'g': re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).replace('\xa0', ' ').strip()})
print(json.dumps(out, ensure_ascii=False, indent=0))
