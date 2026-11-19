"""VERIFICATION PASS 2. Independently written; shares no parsing code with the build or pass 1.
 - xlsx files read as raw OOXML (zipfile + ElementTree, no openpyxl); governor columns found by candidate surname
 - 2026 results ALSO from the SOS NIST 1500-100 XML feed (a different SOS file), matched by GpUnit / party code
 - voter files aggregated with DuckDB SQL (positional columns), not pandas / csv module
 - population from the Census file via DuckDB
Run with the project venv:  .venv/bin/python scripts/verify_pass2.py
"""
import zipfile, re, os, json, glob, datetime, math
import xml.etree.ElementTree as ET
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RAW = os.path.join(ROOT, 'raw')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

def xlsx_sheet(path, title):
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels}
    sh = [s for s in wb.find('m:sheets', NS) if s.get('name') == title][0]
    target = rmap[sh.get(RNS)].lstrip('/'); target = target if target.startswith('xl/') else 'xl/' + target
    grid = {}
    for c in ET.fromstring(z.read(target)).iter('{%s}c' % NS['m']):
        ref = c.get('r'); col = re.match(r'[A-Z]+', ref).group(); row = int(ref[len(col):])
        ci = 0
        for ch in col: ci = ci * 26 + ord(ch) - 64
        v = c.find('m:v', NS); t = c.get('t')
        if t == 'inlineStr': val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
        elif v is None: continue
        elif t == 's': val = ss[int(v.text)]
        elif t == 'str': val = v.text
        else:
            f = float(v.text); val = int(f) if f == int(f) else f
        grid.setdefault(row, {})[ci - 1] = val
    n = max(max(r) for r in grid.values()) + 1
    return [[grid.get(r, {}).get(i) for i in range(n)] for r in sorted(grid)]

def gov_cols(rows, dsur, rsur):
    race, hdr = rows[0], rows[1]
    s = next(i for i, v in enumerate(race) if isinstance(v, str) and 'Governor' in v)
    e = next(i for i in range(s + 1, len(race)) if race[i])
    di = [i for i in range(s, e) if dsur in str(hdr[i]) and '(D)' in str(hdr[i])]
    ri = [i for i in range(s, e) if rsur in str(hdr[i]) and '(R)' in str(hdr[i])]
    assert len(di) == len(ri) == 1
    ci = {h: i for i, h in enumerate(hdr) if isinstance(h, str)}
    out = {}
    for r in rows[2:]:
        if isinstance(r[0], str) and r[0] not in ('Percentage', 'Total'):
            out[r[0]] = dict(D=r[di[0]], R=r[ri[0]], all=sum(x or 0 for x in r[s:e]), reg=r[ci['Registered Voters']],
                             ballots=r[ci['Ballots Counted'] if 'Ballots Counted' in ci else ci['Total Voters']],
                             L=next((r[i] for i in range(s, e) if '(L)' in str(hdr[i])), None))
    return out

x22 = gov_cols(xlsx_sheet(os.path.join(RAW, '2022_statewide-races-summary.xlsx'), 'Statewide Offices'), 'Whaley', 'DeWine')
x26 = gov_cols(xlsx_sheet(os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), 'Statewide Offices'), 'Acton', 'Ramaswamy')
x18 = gov_cols(xlsx_sheet(os.path.join(RAW, 'control_2018', '2018-11-06_statewidecounty_miami.xlsx'), 'Statewide Offices'), 'Cordray', 'DeWine')
pr = xlsx_sheet(os.path.join(RAW, 'crosscheck', '2022-05-03_primary_ballotscastsummaryofficialresults.xlsx'), '5-3-22 Summary Ballots Cast')
ph = pr[1]; p22 = {r[0]: r[ph.index('Democratic Ballots Cast')] for r in pr[2:] if isinstance(r[0], str) and r[0] != 'Total'}

# ---- NIST XML (2026) ----
X = '{http://grouper.ieee.org/groups/1622/groups/2/V1/1622_2-election_results_reporting.xsd}'
XSI = '{http://www.w3.org/2001/XMLSchema-instance}type'
root = ET.parse(os.path.join(RAW, '2026_VSSC1622_NIST1500-100_20261119-1753.xml')).getroot()
gp = {}
for g in root.iter(X + 'GpUnit'):
    if g.get('Type') == 'County' and g.get('VotersRegistered') is not None:   # reporting units (not district defs)
        gp[g.get('ObjectId')] = dict(name=g.get('Name'), reg=int(g.get('VotersRegistered')), ballots=int(g.get('VotersParticipated')))
party = {p.get('ObjectId'): (p.find(X + 'Code').get('Value') if p.find(X + 'Code') is not None else None) for p in root.iter(X + 'Party')}
cand = {c.get('ObjectId'): party.get(c.findtext(X + 'PartyId')) for c in root.iter(X + 'Candidate')}
contest = [c for c in root.iter(X + 'Contest') if c.get('Name') == 'Governor and Lieutenant Governor'][0]
xml26 = {v['name']: dict(D=0, R=0, all=0, reg=v['reg'], ballots=v['ballots']) for v in gp.values()}
for bs in contest.iter(X + 'BallotSelection'):
    p = cand.get(bs.findtext(X + 'CandidateId'))
    for vc in bs.iter(X + 'VoteCounts'):
        u = vc.findtext(X + 'GpUnitId')
        if u in gp:
            n = int(vc.get('Count')); xml26[gp[u]['name']]['all'] += n
            if p == 'D': xml26[gp[u]['name']]['D'] += n
            if p == 'R': xml26[gp[u]['name']]['R'] += n
assert len(xml26) == 88

# ---- voter files with DuckDB ----
con = duckdb.connect()
swg = os.path.join(RAW, 'voterfile_swvf_20261114', 'SWVF_*.txt.gz')
cols = con.execute(f"SELECT * FROM read_csv('{glob.glob(swg)[0]}', all_varchar=true, header=true) LIMIT 0").description
names = [c[0] for c in cols]
def key(c): m, d, y = c.split('-')[1].split('/'); return y + m + d
w22 = sorted([c for c in names if c.startswith('PRIMARY-') and '20200101' <= key(c) <= '20221108'], key=key)
le22 = [c for c in names if c.split('-')[0] in ('PRIMARY', 'GENERAL', 'SPECIAL') and key(c) <= '20221108']
q = lambda c: '"' + c + '"'
# latest non-X party ballot in window: COALESCE from newest to oldest
newest_first = ', '.join(f"CASE WHEN {q(c)} NOT IN ('', 'X') THEN {q(c)} END" for c in reversed(w22))
reg22 = f"(REGISTRATION_DATE <= '2022-10-11' OR " + ' OR '.join(f"{q(c)} <> ''" for c in le22) + ')'
sql = f"""
SELECT CAST(COUNTY_NUMBER AS INT) cn, COUNT(*) tot,
  SUM(CASE WHEN PARTY_AFFILIATION='D' THEN 1 ELSE 0 END) d26,
  SUM(CASE WHEN {reg22} THEN 1 ELSE 0 END) s22,
  SUM(CASE WHEN {reg22} AND COALESCE({newest_first})='D' THEN 1 ELSE 0 END) d22,
  SUM(CASE WHEN "PRIMARY-05/03/2022"='D' THEN 1 ELSE 0 END) sd
FROM read_csv('{swg}', all_varchar=true, header=true, nullstr='\\x01', quote='"', escape='"')
GROUP BY 1 ORDER BY 1"""
sw = {r[0]: r[1:] for r in con.execute(sql).fetchall()}
snapg = os.path.join(RAW, 'datact_snapshot_20261103', 'DS20261103_*.csv')
snap = {}
for f in sorted(glob.glob(snapg)):    # one file at a time, explicit RFC-4180 quoting (run 1 used glob + sniffing: see report)
    for cn_, d_ in con.execute(f"""SELECT CAST(column01 AS INT), SUM(CASE WHEN upper(trim(column12)) IN ('D','DEM') THEN 1 ELSE 0 END)
      FROM read_csv('{f}', all_varchar=true, header=false, skip=1, quote='"', escape='"', strict_mode=true) GROUP BY 1""").fetchall():
        snap[cn_] = snap.get(cn_, 0) + d_
popr = con.execute(f"""SELECT replace(CTYNAME,' County',''), CAST(POPESTIMATE2025 AS INT) FROM read_csv('{os.path.join(RAW, 'census', 'co-est2025-alldata.csv')}', all_varchar=true, encoding='latin-1')
  WHERE STATE='39' AND COUNTY<>'000'""").fetchall(); pop = dict(popr)
counties = sorted(x22); assert len(counties) == 88 and set(counties) == set(xml26) == set(pop)
cnum = {n: i + 1 for i, n in enumerate(sorted(counties, key=str.upper))}

table = con.execute(f"SELECT * FROM read_csv('{os.path.join(ROOT, 'data', 'ohio_88_counties_by_population.csv')}', all_varchar=true)").fetchdf()
checks, disc, notes = 0, [], []
def cmp(c, f, mine, theirs, tol=None):
    global checks; checks += 1
    if isinstance(mine, bool): ok = str(mine) == str(theirs)
    elif tol is None: ok = float(theirs) == float(mine)
    else: ok = math.isclose(float(theirs), mine, abs_tol=tol)
    if not ok: disc.append(dict(county=c, field=f, pass2=mine, table=theirs))
for _, t in table.iterrows():
    c = t['county']; a, b, o, s = x22[c], x26[c], x18[c], sw[cnum[c]]
    # 2026 xlsx vs NIST XML (two different SOS files)
    for k in ('D', 'R', 'all', 'reg', 'ballots'):
        if b[k] != xml26[c][k]: notes.append(f'{c}: 2026 xlsx {k}={b[k]} vs NIST XML {xml26[c][k]}')
    tot, d26, s22, d22s, sd = s
    d22 = round(d22s * p22[c] / sd)
    raw = dict(D22=a['D'], Rep22=a['R'], ballots22=a['ballots'], totreg22=a['reg'], gov_all22=a['all'],
               D26=xml26[c]['D'], Rep26=xml26[c]['R'], ballots26=xml26[c]['ballots'], totreg26=xml26[c]['reg'], gov_all26=xml26[c]['all'],
               Lib26=b['L'], D18=o['D'], ballots18=o['ballots'], population=pop[c], demreg26=d26, swvf26_total=tot,
               recon22_D_survivors=d22s, reg22_survivors=s22, prim22_D_official=p22[c], prim22_D_surviving=sd, demreg22=d22, snap26_D=snap[cnum[c]])
    for k, v in raw.items(): cmp(c, k, v, t[k])
    S22 = a['D'] / a['ballots'] * 100; S26 = xml26[c]['D'] / xml26[c]['ballots'] * 100
    R22 = d22 / a['reg'] * 100; R26 = d26 / xml26[c]['reg'] * 100; S18 = o['D'] / o['ballots'] * 100
    der = dict(S22=S22, S26=S26, R22=R22, R26=R26, G22=S22 - R22, G26=S26 - R26, dG=S26 - R26 - S22 + R22,
               reg_share_loss=R22 - R26, residual=(S26 - R26 - S22 + R22) - (R22 - R26),
               residual_votes=xml26[c]['D'] * 1.0 - S22 * xml26[c]['ballots'] / 100,
               gap_votes_ne_style=xml26[c]['D'] - a['D'] * d26 / d22, S18=S18, residual_1822=S22 - S18)
    for k, v in der.items(): cmp(c, k, v, t[k], tol=6e-4)
    cmp(c, 'overballot_DR22', a['D'] + a['R'] > a['ballots'], t['overballot_DR22'])
    cmp(c, 'overballot_DR26', xml26[c]['D'] + xml26[c]['R'] > xml26[c]['ballots'], t['overballot_DR26'])
    cmp(c, 'overballot_all22', a['all'] > a['ballots'], t['overballot_all22'])
    cmp(c, 'overballot_all26', xml26[c]['all'] > xml26[c]['ballots'], t['overballot_all26'])
summ = json.load(open(os.path.join(ROOT, 'data', 'summary.json')))['statewide']
for k, v in (('D22', sum(x22[c]['D'] for c in counties)), ('Rep22', sum(x22[c]['R'] for c in counties)), ('ballots22', sum(x22[c]['ballots'] for c in counties)),
             ('totreg22', sum(x22[c]['reg'] for c in counties)), ('D26', sum(xml26[c]['D'] for c in counties)), ('Rep26', sum(xml26[c]['R'] for c in counties)),
             ('ballots26', sum(xml26[c]['ballots'] for c in counties)), ('totreg26', sum(xml26[c]['reg'] for c in counties)),
             ('demreg22', sum(round(sw[cnum[c]][3] * p22[c] / sw[cnum[c]][4]) for c in counties)), ('demreg26', sum(sw[cnum[c]][1] for c in counties))):
    cmp('STATEWIDE', k, v, summ[k])
rep = dict(pass_name='Pass 2 (raw OOXML via zipfile/ElementTree; SOS NIST 1500-100 XML for 2026; DuckDB SQL for voter files)',
           run=datetime.datetime.now().strftime('%Y-%m-%d %H:%M CST'), counties=len(table), figures_checked=checks,
           matched=checks - len(disc), mismatched=len(disc), discrepancies=disc, notes_xlsx_vs_xml_2026=notes,
           earlier_runs=['run 1 (12:25 CST): 3,440 of 3,442 matched; 2 mismatches, both snap26_D (Mahoning 24,034 vs 24,073; Clark 8,609 vs 8,610). Cause: pass-2 code read all 88 snapshot files in one DuckDB glob with auto-sniffed escape character (backslash), which mis-split a few quoted fields. Fixed by reading each file with explicit RFC-4180 quoting; raw files unchanged. See pass2_report_run1_superseded.json.'])
json.dump(rep, open(os.path.join(ROOT, 'verification', 'pass2_report.json'), 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in rep.items() if k not in ('discrepancies',)}, default=str), disc[:20])
