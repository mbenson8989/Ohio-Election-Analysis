"""RAW-SOURCE cell check of Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf.

Written independently of build_data.py / aggregate_voterfiles.py / build_pdf.py / verify_pass*.py.
Reads ONLY raw SOS files (never data/*.csv, data/*.json or any processed table):
  raw/2022_statewide-races-summary.xlsx                    2022 official canvass (governor, Registered Voters, Ballots Counted)
  raw/11032026GenUnTotCanSumm11192026-1753.xlsx            2026 UNOFFICIAL canvass
  raw/2026_VSSC1622_NIST1500-100_20261119-1753.xml         2026 NIST XML feed (second 2026 source, must agree with the xlsx)
  raw/crosscheck/2022-05-03_primary_ballotscastsummaryofficialresults.xlsx   official May 2022 primary ballots by party
  raw/voterfile_swvf_20261114/SWVF_*.txt.gz                SOS statewide voter file (14-NOV-26), streamed with the csv module
XLSX are parsed straight from the OOXML zip (no openpyxl / pandas). Values are recomputed with exact rational arithmetic and
rounded half-up to the decimals the PDF displays; then each PDF cell (pdftotext -layout) is compared as a string.

Definitions recomputed:
  Dem affil 2026  = voter-file records with PARTY_AFFILIATION == 'D'
  Share 2026 %    = Dem affil 2026 / 2026 canvass Registered Voters
  Dem affil 2022  = round( N_recon22 * May22_official_D / May22_surviving_D ), where N_recon22 = records registered for Nov 8 2022
                    (REGISTRATION_DATE <= 2022-10-11 or any history mark dated <= 2022-11-08) whose most recent partisan primary
                    ballot (PRIMARY-* column dated 2020-01-01..2022-11-08, value not blank / 'X') is D  (R.C. 3513.19)
  Votes           = Democratic governor candidate (Whaley 2022, Acton 2026); Ballots = SOS 'Ballots Counted'
  Change # = new - old;  Change % = (new - old) / old * 100
"""
import gzip, csv, glob, io, json, os, re, subprocess, sys, zipfile, datetime
import xml.etree.ElementTree as ET
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
PDF = os.path.join(ROOT, 'Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf')
OUTJ = os.path.join(ROOT, 'verification', 'pdf_raw_check.json')
OUTT = os.path.join(ROOT, 'verification', 'pdf_raw_check.txt')
csv.field_size_limit(10 ** 9)

# ---------------- OOXML reader (no third-party libs) ----------------
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def col_index(ref):
    letters = re.match(r'[A-Z]+', ref).group(0); n = 0
    for ch in letters: n = n * 26 + ord(ch) - 64
    return n - 1
def read_sheet(path, sheet_name):
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rid = next(s.get('{%s}id' % NS['r']) for s in wb.find('m:sheets', NS) if s.get('name') == sheet_name)
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    target = next(r.get('Target') for r in rels if r.get('Id') == rid)
    target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
    rows = []
    for row in ET.fromstring(z.read(target)).iter('{%s}row' % NS['m']):
        vals = {}
        for c in row.findall('m:c', NS):
            t = c.get('t'); v = c.find('m:v', NS)
            if t == 'inlineStr':
                val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
            elif v is None: continue
            elif t == 's': val = ss[int(v.text)]
            elif t in ('str', 'e'): val = v.text
            elif t == 'b': val = v.text
            else:
                val = Fraction(v.text)
                if val.denominator == 1: val = int(val)
            vals[col_index(c.get('r'))] = val
        rows.append([vals.get(i) for i in range(max(vals) + 1)] if vals else [])
    return rows

def canvass(path, dem_prefix):
    rows = read_sheet(path, 'Statewide Offices')
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == 'County Name')
    hdr = rows[hdr_i]; top = rows[hdr_i - 1]
    g0 = next(i for i, v in enumerate(top) if isinstance(v, str) and v.strip().startswith('Governor and Lieutenant Governor'))
    g1 = next((i for i in range(g0 + 1, len(top)) if top[i] not in (None, '')), len(hdr))
    dcol = [i for i in range(g0, g1) if isinstance(hdr[i], str) and hdr[i].startswith(dem_prefix) and hdr[i].endswith('(D)')]
    assert len(dcol) == 1, dcol
    reg_c, bal_c = hdr.index('Registered Voters'), hdr.index('Ballots Counted')
    out = {}
    for r in rows[hdr_i + 1:]:
        if not r or not isinstance(r[0], str) or r[0] == 'Percentage': continue
        out[r[0].strip()] = dict(reg=r[reg_c], ballots=r[bal_c], D=r[dcol[0]])
    return out

# ---------------- voter-file worker ----------------
def hdate(col):
    k, d = col.split('-', 1); mm, dd, yy = d.split('/'); return k, datetime.date(int(yy), int(mm), int(dd))
def scan_swvf(path):
    res = {}
    with gzip.open(path, 'rt', encoding='latin-1', newline='') as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        ix = {h: i for i, h in enumerate(hdr)}
        hist = [(i, *hdate(h)) for i, h in enumerate(hdr) if re.match(r'^(PRIMARY|GENERAL|SPECIAL)-\d\d/\d\d/\d{4}$', h)]
        cut22 = datetime.date(2022, 11, 8)
        hist_le = [i for i, k, d in hist if d <= cut22]
        prim22 = [i for i, k, d in sorted(hist, key=lambda x: x[2]) if k == 'PRIMARY' and datetime.date(2020, 1, 1) <= d <= cut22]
        may22 = ix['PRIMARY-05/03/2022']
        ci, ri, pi = ix['COUNTY_NUMBER'], ix['REGISTRATION_DATE'], ix['PARTY_AFFILIATION']
        for rec in rd:
            c = int(rec[ci])
            a = res.get(c)
            if a is None: a = res[c] = dict(records=0, aff26_D=0, recon22_D=0, reg22=0, may22_D=0)
            a['records'] += 1
            if rec[pi].strip().upper() == 'D': a['aff26_D'] += 1
            if rec[may22].strip().upper() == 'D': a['may22_D'] += 1
            registered = rec[ri] <= '2022-10-11' or any(rec[i] != '' for i in hist_le)
            if not registered: continue
            a['reg22'] += 1
            last = ''
            for i in reversed(prim22):
                v = rec[i].strip().upper()
                if v and v != 'X': last = v; break
            if last == 'D': a['recon22_D'] += 1
    return os.path.basename(path), res

def q(x, places):  # exact Fraction/int -> Decimal rounded half-up
    d = Decimal(x.numerator) / Decimal(x.denominator) if isinstance(x, Fraction) else Decimal(x)
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
def tie(x, places):
    f = Fraction(x) * 10 ** places; return (f - int(f)) == Fraction(1, 2) or (f - int(f)) == Fraction(-1, 2)
def fn(v): return f'{v:,}'
def fs(v): return f'{v:+,}'
def fp(x): s = q(x, 1); return ('+' if s >= 0 else '') + f'{s}%' if not (s == 0 and x < 0) else f'-{abs(s)}%'
def fsh(x): return f'{q(x, 1)}%'

def main():
    t0 = datetime.datetime.now()
    c22 = canvass(os.path.join(RAW, '2022_statewide-races-summary.xlsx'), 'Nan Whaley')
    c26 = canvass(os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), 'Amy Acton')
    counties = sorted(k for k in c22 if k != 'Total')
    assert len(counties) == 88 and counties == sorted(k for k in c26 if k != 'Total')
    # May 2022 primary
    prow = read_sheet(os.path.join(RAW, 'crosscheck', '2022-05-03_primary_ballotscastsummaryofficialresults.xlsx'), '5-3-22 Summary Ballots Cast')
    ph_i = next(i for i, r in enumerate(prow) if r and 'Democratic Ballots Cast' in r)
    dci = prow[ph_i].index('Democratic Ballots Cast')
    may = {r[0].strip(): r[dci] for r in prow[ph_i + 1:] if r and isinstance(r[0], str) and r[0].strip() in counties}
    assert len(may) == 88
    # NIST XML second source for 2026
    X = '{http://grouper.ieee.org/groups/1622/groups/2/V1/1622_2-election_results_reporting.xsd}'
    root = ET.parse(os.path.join(RAW, '2026_VSSC1622_NIST1500-100_20261119-1753.xml')).getroot()
    units = {g.get('ObjectId'): g for g in root.iter(X + 'GpUnit') if g.get('Type') == 'County' and g.get('VotersRegistered') is not None}
    pcode = {}
    for p in root.iter(X + 'Party'):
        cd = p.find(X + 'Code'); pcode[p.get('ObjectId')] = cd.get('Value') if cd is not None else None
    cparty = {c.get('ObjectId'): pcode.get(c.findtext(X + 'PartyId')) for c in root.iter(X + 'Candidate')}
    gov = next(c for c in root.iter(X + 'Contest') if c.get('Name') == 'Governor and Lieutenant Governor')
    xD = {}
    for bs in gov.iter(X + 'BallotSelection'):
        if cparty.get(bs.findtext(X + 'CandidateId')) != 'DEM' and cparty.get(bs.findtext(X + 'CandidateId')) != 'D': continue
        for vc in bs.iter(X + 'VoteCounts'):
            u = vc.findtext(X + 'GpUnitId')
            if u in units: xD[u] = xD.get(u, 0) + int(vc.get('Count'))
    xml_mism = []
    for u, g in units.items():
        nm = g.get('Name').strip()
        nm = next((c for c in counties if c.upper() == nm.upper()), nm)
        if nm not in c26: xml_mism.append(('unknown unit', nm)); continue
        for k, xv in (('reg', int(g.get('VotersRegistered'))), ('ballots', int(g.get('VotersParticipated'))), ('D', xD.get(u))):
            if c26[nm][k] != xv: xml_mism.append((nm, k, c26[nm][k], xv))
    xml_units = len(units)
    # voter files (parallel, one process per file)
    files = sorted(glob.glob(os.path.join(RAW, 'voterfile_swvf_20261114', 'SWVF_*.txt.gz')))
    assert len(files) == 4
    with Pool(4) as pool: parts = pool.map(scan_swvf, files)
    vf = {}
    for _, res in parts:
        for c, a in res.items():
            assert c not in vf, ('county in two files', c); vf[c] = a
    assert sorted(vf) == list(range(1, 89))
    num = {c: i + 1 for i, c in enumerate(sorted(counties, key=str.upper))}   # SOS county numbers are alphabetical
    # ---- recompute ----
    R = {}
    for c in counties:
        a = vf[num[c]]
        d22_exact = Fraction(a['recon22_D'] * may[c], a['may22_D'])
        d22 = int(q(d22_exact, 0))
        R[c] = dict(d22=d22, d22_tie=tie(d22_exact, 0), d26=a['aff26_D'], reg26=c26[c]['reg'], v22=c22[c]['D'], v26=c26[c]['D'],
                    b22=c22[c]['ballots'], b26=c26[c]['ballots'], raw=dict(a, may22_official_D=may[c], d22_exact=float(d22_exact)))
    T = {k: sum(R[c][k] for c in counties) for k in ('d22', 'd26', 'reg26', 'v22', 'v26', 'b22', 'b26')}
    canv_tot = [('2022 Total D', T['v22'], c22['Total']['D']), ('2022 Total ballots', T['b22'], c22['Total']['ballots']),
                ('2026 Total D', T['v26'], c26['Total']['D']), ('2026 Total ballots', T['b26'], c26['Total']['ballots']),
                ('2026 Total reg', T['reg26'], c26['Total']['reg'])]
    def cells(r):
        return [fsh(Fraction(r['d26'], r['reg26']) * 100), fn(r['d22']), fn(r['d26']), fs(r['d26'] - r['d22']), fp(Fraction(r['d26'] - r['d22'], r['d22']) * 100),
                fn(r['v22']), fn(r['v26']), fs(r['v26'] - r['v22']), fp(Fraction(r['v26'] - r['v22'], r['v22']) * 100),
                fn(r['b22']), fn(r['b26']), fs(r['b26'] - r['b22']), fp(Fraction(r['b26'] - r['b22'], r['b22']) * 100)]
    COLS = ['Dem Affil Share 2026 %', 'Dem Affil 2022 (est.)', 'Dem Affil 2026', 'Affil Change #', 'Affil Change %',
            'Dem Gov Votes 2022', 'Dem Gov Votes 2026*', 'Vote Change #', 'Vote Change %', 'Total Ballots 2022', 'Total Ballots 2026*',
            'Ballot Change #', 'Ballot Change %']
    ties = []
    for c in counties:
        r = R[c]
        for nm, x in (('share', Fraction(r['d26'], r['reg26']) * 100), ('affil%', Fraction(r['d26'] - r['d22'], r['d22']) * 100),
                      ('vote%', Fraction(r['v26'] - r['v22'], r['v22']) * 100), ('ballot%', Fraction(r['b26'] - r['b22'], r['b22']) * 100)):
            if tie(x, 1): ties.append((c, nm))
        if r['d22_tie']: ties.append((c, 'd22 rounding'))
    # ---- PDF ----
    txt = subprocess.run(['pdftotext', '-layout', PDF, '-'], capture_output=True, text=True, check=True).stdout
    pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', PDF], capture_output=True, text=True).stdout).group(1))
    TOK = r'([+-]?[\d,]+(?:\.\d)?%?)'
    rx = re.compile(r'^\s*([A-Z][A-Za-z .]+?)\s{2,}' + r'\s+'.join([TOK] * 13) + r'\s*$')
    prow_ = []
    for line in txt.splitlines():
        m = rx.match(line)
        if m: prow_.append((m.group(1).strip(), list(m.groups()[1:])))
    names = [n for n, _ in prow_]
    issues = []
    if len(prow_) != 89: issues.append(f'PDF table rows parsed: {len(prow_)} (expected 89)')
    if sorted(n for n in names if n != 'Statewide total') != counties: issues.append('PDF county set differs from canvass county set')
    checked = matched = 0; mism = []
    for n, vals in prow_:
        exp = cells(T | {'d22': T['d22']}) if n == 'Statewide total' else cells(R[n])
        for col, pv, ev in zip(COLS, vals, exp):
            checked += 1
            if pv == ev: matched += 1
            else: mism.append(dict(county=n, column=col, pdf=pv, raw=ev))
    # sort order: share desc, ties by name
    exp_order = sorted(counties, key=lambda c: (-Fraction(R[c]['d26'], R[c]['reg26']), c))
    order_ok = [n for n in names if n != 'Statewide total'] == exp_order and names[-1] == 'Statewide total'
    checked += 1; matched += order_ok
    if not order_ok: mism.append(dict(county='(all)', column='row order', pdf=names, raw=exp_order))
    # narrative numbers in the header/legend
    flat = re.sub(r'\s+', ' ', txt)
    rose = [c for c in exp_order if R[c]['d26'] > R[c]['d22']]
    wy = R['Wyandot']; DR_wy = None
    narrative = [('legend: counties where affiliation rose', f'Democratic affiliation rose ({len(rose)}: {", ".join(rose)})'),
                 ('Wyandot ballots counted 2026', f"ballots counted ({fn(wy['b26'])})"),
                 ('Cuyahoga 2022 estimate in footnote', f"{fn(R['Cuyahoga']['d22'])} estimated"),
                 ('leader by share', f'{exp_order[0]} leads by share'),
                 ('leader by raw affiliation', f"{max(counties, key=lambda c: R[c]['d26'])} leads by raw Democratic affiliation"),
                 ('page count in footer', f'Page {pages} of {pages}')]
    # Wyandot D+R needs the Republican column: read it from the same raw 2026 sheet
    rows26 = read_sheet(os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), 'Statewide Offices')
    h_i = next(i for i, r in enumerate(rows26) if r and r[0] == 'County Name')
    rc = next(i for i, v in enumerate(rows26[h_i]) if isinstance(v, str) and v.startswith('Vivek Ramaswamy') and v.endswith('(R)'))
    wy_rep = next(r[rc] for r in rows26[h_i + 1:] if r and r[0] == 'Wyandot')
    narrative.append(('Wyandot D+R governor votes 2026', f"governor votes ({fn(wy['v26'] + wy_rep)})"))
    for label, s in narrative:
        checked += 1
        if s in flat: matched += 1
        else: mism.append(dict(county='(narrative)', column=label, pdf='not found in PDF text', raw=s))
    rep = dict(generated=t0.isoformat(timespec='seconds'), runtime_s=round((datetime.datetime.now() - t0).total_seconds(), 1),
               pdf=os.path.basename(PDF), pdf_pages=pages, table_rows=len(prow_), cells_checked=checked, cells_matched=matched,
               mismatches=mism, structural_issues=issues, rounding_ties=ties,
               xml_vs_xlsx_2026=dict(units=xml_units, fields_compared=3 * xml_units, mismatches=xml_mism),
               county_sum_vs_canvass_total=[dict(item=a, county_sum=b, canvass_total=c, ok=b == c) for a, b, c in canv_tot],
               statewide=dict(T, share26_pct=str(q(Fraction(T['d26'], T['reg26']) * 100, 2))),
               voterfile_records=sum(v['records'] for v in vf.values()),
               sources=[os.path.relpath(p, ROOT) for p in [os.path.join(RAW, f) for f in ('2022_statewide-races-summary.xlsx', '11032026GenUnTotCanSumm11192026-1753.xlsx', '2026_VSSC1622_NIST1500-100_20261119-1753.xml', 'crosscheck/2022-05-03_primary_ballotscastsummaryofficialresults.xlsx')] + files],
               per_county_raw={c: dict(R[c]['raw'], county_number=num[c]) for c in counties})
    json.dump(rep, open(OUTJ, 'w'), indent=1)
    ok = not mism and not issues and not xml_mism and all(x[1] == x[2] for x in canv_tot)
    lines = [f'Ohio 88-county PDF: raw-source cell check ({rep["generated"]}, America/Chicago)',
             f'PDF pages: {pages}; table rows parsed: {len(prow_)}',
             f'Cells checked: {checked}  matched: {matched}  mismatched: {len(mism)}',
             f'2026 xlsx vs NIST XML: {3 * xml_units} fields, {len(xml_mism)} mismatches',
             'County sums vs canvass Total row: ' + ', '.join(f"{a} {'OK' if b == c else 'DIFF'}" for a, b, c in canv_tot),
             f'Exact rounding ties (half-up applied): {ties or "none"}',
             f'Statewide: {json.dumps(rep["statewide"])}', f'Voter-file records scanned: {rep["voterfile_records"]:,}',
             'RESULT: ' + ('ALL CELLS MATCH RAW SOURCES' if ok else 'MISMATCHES FOUND - DO NOT PUBLISH')]
    for m in mism: lines.append(f"MISMATCH {m['county']} | {m['column']} | PDF {m['pdf']} | raw {m['raw']}")
    for i in issues: lines.append('ISSUE ' + i)
    open(OUTT, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
