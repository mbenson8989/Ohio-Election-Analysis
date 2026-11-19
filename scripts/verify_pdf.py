"""Extract the PDF text with pdftotext and check every cell against values recomputed here from the verified CSV (not from build_pdf's output)."""
import os, subprocess, json, re
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf')
txt = subprocess.run(['pdftotext', '-layout', PDF, '-'], capture_output=True, text=True, check=True).stdout
t = pd.read_csv(os.path.join(ROOT, 'data', 'ohio_88_counties_by_population.csv'))
def exp(name, d22, d26, reg26, v22, v26, b22, b26):
    out = [round(d26 / reg26 * 100, 1), d22, d26, d26 - d22, round((d26 - d22) / d22 * 100, 1), v22, v26, v26 - v22, round((v26 - v22) / v22 * 100, 1), b22, b26, b26 - b22, round((b26 - b22) / b22 * 100, 1)]
    return out
E_ = {r.county: exp(r.county, r.demreg22, r.demreg26, r.totreg26, r.D22, r.D26, r.ballots22, r.ballots26) for r in t.itertuples()}
s = t.sum(numeric_only=True)
E_['Statewide total'] = exp('Statewide total', s.demreg22, s.demreg26, s.totreg26, s.D22, s.D26, s.ballots22, s.ballots26)
def num(tok): return float(tok.replace(',', '').replace('%', '').replace('+', ''))
found, checked, matched, bad, order = set(), 0, 0, [], []
names = sorted(E_, key=len, reverse=True)
for line in txt.split('\n'):
    l = line.strip()
    nm = next((n for n in names if l.startswith(n + ' ')), None)
    if not nm: continue
    toks = l[len(nm):].split()
    if len(toks) != 13 or not all(re.fullmatch(r'[+-]?[\d,]+(\.\d)?%?', x) for x in toks): continue
    found.add(nm); order.append(nm)
    for k, (tok, e) in enumerate(zip(toks, E_[nm])):
        checked += 1
        if abs(num(tok) - float(e)) < 1e-9: matched += 1
        else: bad.append((nm, k, tok, e))
    checked += 1; matched += 1   # county label itself
missing = set(E_) - found
srt = t.assign(sh=t.demreg26 / t.totreg26).sort_values('sh', ascending=False).county.tolist()
order_ok = order[:-1] == srt and order[-1] == 'Statewide total'
pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', PDF], capture_output=True, text=True).stdout).group(1))
hdr_pages = txt.count('Dem Gov Votes'); unoff = txt.count('UNOFFICIAL')
rep = dict(rows_found=len(found), rows_expected=len(E_), missing=sorted(missing), cells_checked=checked, cells_matched=matched, mismatches=bad,
           sort_order_ok=order_ok, pages=pages, header_rows_seen=hdr_pages // 2, unofficial_mentions=unoff)
json.dump(rep, open(os.path.join(ROOT, 'verification', 'pdf_text_check.json'), 'w'), indent=1, default=str); print(rep)
