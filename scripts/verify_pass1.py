"""VERIFICATION PASS 1. Re-reads every raw SOS file with code separate from the build:
 - results: openpyxl, the 'Master' sheet (the build reads 'Statewide Offices'); 2022 ballots/registered also from the
   separate SOS turnout summary file; 2018 from the Master sheet of the amended canvass
 - voter files: Python csv module streaming (the build uses pandas), snapshot + SWVF
Recomputes every derived figure from these values and compares with data/ohio_88_counties_by_population.csv.
"""
import csv, gzip, glob, io, json, os, sys, datetime
import openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RAW = os.path.join(ROOT, 'raw')
csv.field_size_limit(10 ** 9)

def master(path, race_prefix, dname, rname, extra=()):
    rows = list(openpyxl.load_workbook(path, read_only=True, data_only=True)['Master'].iter_rows(values_only=True))
    race, hdr = rows[0], rows[1]
    s = [i for i, v in enumerate(race) if v and str(v).startswith(race_prefix)][0]
    e = next(i for i in range(s + 1, len(race)) if race[i])
    out = {}
    for r in rows[2:]:
        if r[0] in (None, 'Total', 'Percentage'): continue
        c = dict(zip(hdr[s:e], r[s:e]))
        out[r[0]] = dict(reg=r[3], ballots=r[4], D=c[dname], R=c[rname], all=sum(c.values()), **{k: c[v] for k, v in extra})
    return out
m22 = master(os.path.join(RAW, '2022_statewide-races-summary.xlsx'), 'Governor', 'Nan Whaley and Cheryl L. Stephens (D)', 'Mike DeWine and Jon Husted (R)')
m26 = master(os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), 'Governor', 'Amy Acton and David Pepper (D)',
             'Vivek Ramaswamy and Robert A. McColley (R)', extra=(('L', 'Don Kissick and James L. Mills (L)'),))
m18 = master(os.path.join(RAW, 'control_2018', '2018-11-06_statewidecounty_miami.xlsx'), 'Governor', 'Richard Cordray and Betty Sutton (D)', 'Mike DeWine and Jon Husted (R)')
t22 = {r[0]: (r[3], r[4]) for r in openpyxl.load_workbook(os.path.join(RAW, '2022_11-8-22-voter-turnout-summary.xlsx'), read_only=True).worksheets[0].iter_rows(values_only=True) if r[0] in m22}
p22 = {r[0]: (r[5], r[6]) for r in openpyxl.load_workbook(os.path.join(RAW, 'crosscheck', '2022-05-03_primary_ballotscastsummaryofficialresults.xlsx'), read_only=True).worksheets[0].iter_rows(values_only=True) if r[0] in m22}
assert len(m22) == len(m26) == len(m18) == len(t22) == len(p22) == 88
names = sorted(m22, key=str.upper); num2name = {i + 1: n for i, n in enumerate(names)}

# ---- SWVF, csv module
sw = {n: dict(D26=0, R26=0, tot=0, s22=0, d22=0, sd=0) for n in names}
for f in sorted(glob.glob(os.path.join(RAW, 'voterfile_swvf_20261114', 'SWVF_*.txt.gz'))):
    with gzip.open(f, 'rt', newline='', encoding='latin-1') as fh:
        rd = csv.reader(fh); h = next(rd); ix = {k: i for i, k in enumerate(h)}
        def d8(k): mo, dy, yr = k.split('-')[1].split('/'); return yr + mo + dy
        hist = [(d8(k), ix[k], k.startswith('PRIMARY')) for k in h if k[:7] in ('PRIMARY', 'GENERAL', 'SPECIAL')]
        win22 = sorted((d, i) for d, i, p in hist if p and '20200101' <= d <= '20221108')
        le22 = [i for d, i, p in hist if d <= '20221108']
        icn, ireg, ipa, imay = ix['COUNTY_NUMBER'], ix['REGISTRATION_DATE'], ix['PARTY_AFFILIATION'], ix['PRIMARY-05/03/2022']
        for row in rd:
            c = sw[num2name[int(row[icn])]]
            c['tot'] += 1; pa = row[ipa]
            if pa == 'D': c['D26'] += 1
            elif pa == 'R': c['R26'] += 1
            if row[ireg] <= '2022-10-11' or any(row[i] for i in le22):
                c['s22'] += 1
                last = None
                for d, i in win22:
                    if row[i] and row[i] != 'X': last = row[i]
                if last == 'D': c['d22'] += 1
            if row[imay] == 'D': c['sd'] += 1
    print('swvf', os.path.basename(f), flush=True)
# ---- snapshot, csv module
snap = {}
for f in sorted(glob.glob(os.path.join(RAW, 'datact_snapshot_20261103', 'DS20261103_*.csv'))):
    with open(f, newline='', encoding='latin-1') as fh:
        rd = csv.reader(fh); h = [x.replace('\xef\xbb\xbf', '').upper() for x in next(rd)]
        ip, ic = h.index('PARTY_AFFILIATION'), h.index('COUNTY_NUMBER'); n = 0; cn = None
        for row in rd:
            v = row[ip].strip().upper(); n += v in ('D', 'DEM'); cn = int(row[ic])
        snap[num2name[cn]] = n
pop = {r['CTYNAME'].replace(' County', ''): int(r['POPESTIMATE2025']) for r in csv.DictReader(open(os.path.join(RAW, 'census', 'co-est2025-alldata.csv'), encoding='latin-1')) if r['STATE'] == '39' and r['COUNTY'] != '000'}

table = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'ohio_88_counties_by_population.csv'))))
assert len(table) == 88
checks = []; disc = []
def chk(county, field, mine, theirs, tol=0):
    theirs_v = theirs
    if isinstance(mine, bool): ok = str(mine) == theirs
    elif tol == 0: ok = int(float(theirs)) == mine and float(theirs) == int(float(theirs))
    else: ok = abs(float(theirs) - mine) <= tol
    checks.append(ok)
    if not ok: disc.append(dict(county=county, field=field, pass1=mine, table=theirs_v))
for t in table:
    c = t['county']; a, b, o, s = m22[c], m26[c], m18[c], sw[c]
    assert t22[c] == (a['reg'], a['ballots']), c        # two SOS 2022 files agree
    demreg22 = round(s['d22'] * p22[c][0] / s['sd'])
    v = dict(D22=a['D'], Rep22=a['R'], ballots22=a['ballots'], totreg22=a['reg'], gov_all22=a['all'],
             D26=b['D'], Rep26=b['R'], ballots26=b['ballots'], totreg26=b['reg'], gov_all26=b['all'], Lib26=b['L'],
             D18=o['D'], ballots18=o['ballots'], population=pop[c], demreg26=s['D26'], repreg26=s['R26'], swvf26_total=s['tot'],
             recon22_D_survivors=s['d22'], reg22_survivors=s['s22'], prim22_D_official=p22[c][0], prim22_D_surviving=s['sd'],
             demreg22=demreg22, snap26_D=snap[c])
    for k, x in v.items(): chk(c, k, x, t[k])
    S22 = 100 * a['D'] / a['ballots']; S26 = 100 * b['D'] / b['ballots']; R22 = 100 * demreg22 / a['reg']; R26 = 100 * s['D26'] / b['reg']
    der = dict(S22=S22, S26=S26, R22=R22, R26=R26, G22=S22 - R22, G26=S26 - R26, dG=(S26 - R26) - (S22 - R22),
               reg_share_loss=R22 - R26, residual=S26 - S22, residual_votes=b['D'] - S22 / 100 * b['ballots'],
               gap_votes_ne_style=b['D'] - a['D'] * s['D26'] / demreg22, S18=100 * o['D'] / o['ballots'],
               residual_1822=S22 - 100 * o['D'] / o['ballots'])
    for k, x in der.items(): chk(c, k, x, t[k], tol=6e-4)
    for y, r in (('22', a), ('26', b)):
        chk(c, 'overballot_DR' + y, r['D'] + r['R'] > r['ballots'], t['overballot_DR' + y])
        chk(c, 'overballot_all' + y, r['all'] > r['ballots'], t['overballot_all' + y])
# statewide totals against SOS Total rows
summ = json.load(open(os.path.join(ROOT, 'data', 'summary.json')))['statewide']
for path, y, dn, rn in ((os.path.join(RAW, '2022_statewide-races-summary.xlsx'), '22', 'Nan Whaley and Cheryl L. Stephens (D)', 'Mike DeWine and Jon Husted (R)'),
                        (os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), '26', 'Amy Acton and David Pepper (D)', 'Vivek Ramaswamy and Robert A. McColley (R)')):
    rows = list(openpyxl.load_workbook(path, read_only=True)['Master'].iter_rows(values_only=True)); hdr = rows[1]; tot = rows[2]
    for k, col in (('D', dn), ('Rep', rn)): chk('STATEWIDE', k + y, tot[hdr.index(col)], str(summ[k + y]))
    chk('STATEWIDE', 'ballots' + y, tot[4], str(summ['ballots' + y])); chk('STATEWIDE', 'totreg' + y, tot[3], str(summ['totreg' + y]))
rep = dict(pass_name='Pass 1 (openpyxl Master sheet + SOS turnout file; Python csv module for voter files)',
           run=datetime.datetime.now().strftime('%Y-%m-%d %H:%M CST'), counties=len(table), figures_checked=len(checks),
           matched=sum(checks), mismatched=len(checks) - sum(checks), discrepancies=disc)
json.dump(rep, open(os.path.join(ROOT, 'verification', 'pass1_report.json'), 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in rep.items() if k != 'discrepancies'}), disc[:20])
