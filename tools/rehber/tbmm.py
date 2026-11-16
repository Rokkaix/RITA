"""TBMM'nin resmî milletvekili listesini (tbmm.gov.tr/milletvekili/AllList) okur -> JSON."""
import sys, re, json, html, subprocess
def tr_title(w):
    def one(x):
        if not x: return x
        low = x[1:].replace('I', 'ı').replace('İ', 'i').lower()
        return x[0] + low
    return ' '.join('-'.join(one(p) for p in t.split('-')) for t in w.split())
def name_fix(n):
    parts = n.split()
    return ' '.join(p if not p.isupper() or len(p) < 2 else tr_title(p) for p in parts)
if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else None
    s = open(src, encoding='utf-8').read() if src else subprocess.run(['curl', '-s', '-m', '60', '-A', 'Mozilla/5.0', 'https://tbmm.gov.tr/milletvekili/AllList'], capture_output=True, text=True).stdout
    out, il = [], None
    for m in re.finditer(r'<li class="list-group-item ([^"]*)"[^>]*>(.*?)</li>', s, re.S):
        cls, body = m.group(1), m.group(2)
        if 'active' in cls:
            il = html.unescape(re.sub(r'<[^>]+>', '', body)).strip()
            continue
        a = re.search(r'>([^<]+)</a>', body)
        p = re.search(r'text-right">\s*([^<]+?)\s*</div>', body)
        if a and il:
            out.append({'n': name_fix(html.unescape(a.group(1)).strip()), 'il': tr_title(il), 'parti': html.unescape(p.group(1)).strip() if p else ''})
    print(json.dumps(out, ensure_ascii=False, indent=0))
