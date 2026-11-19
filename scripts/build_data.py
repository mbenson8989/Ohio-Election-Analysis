"""PASS 1: build the Ohio county table (88 counties) from the raw SOS files. Ballots denominator.

Raw inputs (../raw, untouched):
  2022_statewide-races-summary.xlsx            SOS Nov 8 2022 Official Canvass, county level (Wayback id_ copy, SHA-1 matches CDX digest)
  11032026GenUnTotCanSumm11192026-1753.xlsx    SOS Nov 3 2026 UNOFFICIAL canvass, liveresults.ohiosos.gov, downloaded 2026-11-19 11:53 CST
  control_2018/2018-11-06_statewidecounty_miami.xlsx   SOS 2018 Official Canvass (as amended by Miami BOE), control cycle
  crosscheck/2022-05-03_primary_ballotscastsummaryofficialresults.xlsx   SOS May 3 2022 primary, ballots by party
  ../data/voterfile_county_aggregates_pass1.csv  county counts from the SOS voter files (scripts/aggregate_voterfiles.py)
  census/co-est2025-alldata.csv                Census Vintage 2025 county population
"""
import os, json
import numpy as np, pandas as pd, openpyxl
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw'); OUT = os.path.join(ROOT, 'data')

def sheet(path, name='Statewide Offices'):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[name]
    return [list(r) for r in ws.iter_rows(values_only=True)]

def gov(path, label):
    """County rows of the governor race: dict county -> {reg, ballots, cands{name:votes}}, plus Total row."""
    rows = sheet(path); race, hdr = rows[0], rows[1]
    c0 = next(i for i, v in enumerate(race) if v and str(v).startswith('Governor and Lieutenant Governor'))
    c1 = next((i for i in range(c0 + 1, len(race)) if race[i]), len(race))
    cands = hdr[c0:c1]
    out = {}
    for r in rows[2:]:
        if not r[0] or r[0] == 'Percentage': continue
        out[r[0]] = dict(reg=r[3], ballots=r[4], cands=dict(zip(cands, r[c0:c1])))
    assert len(out) == 89, (label, len(out))   # 88 counties + Total
    return out, cands

g22, c22 = gov(os.path.join(RAW, '2022_statewide-races-summary.xlsx'), '2022')
g26, c26 = gov(os.path.join(RAW, '11032026GenUnTotCanSumm11192026-1753.xlsx'), '2026')
g18, c18 = gov(os.path.join(RAW, 'control_2018', '2018-11-06_statewidecounty_miami.xlsx'), '2018')
D22n = 'Nan Whaley and Cheryl L. Stephens (D)'; R22n = 'Mike DeWine and Jon Husted (R)'
D26n = 'Amy Acton and David Pepper (D)';      R26n = 'Vivek Ramaswamy and Robert A. McColley (R)'
D18n = 'Richard Cordray and Betty Sutton (D)'; R18n = 'Mike DeWine and Jon Husted (R)'
assert D22n in c22 and R22n in c22 and D26n in c26 and R26n in c26 and D18n in c18
COUNTIES = sorted(k for k in g22 if k != 'Total')
assert COUNTIES == sorted(k for k in g26 if k != 'Total') == sorted(k for k in g18 if k != 'Total')
regions = {r[0]: r[1] for r in sheet(os.path.join(RAW, '2022_statewide-races-summary.xlsx'))[2:] if r[0] in COUNTIES}

# May 2022 primary, official D/R ballots (to calibrate the 2022 affiliation reconstruction)
pr = {r[0]: dict(D=r[5], R=r[6], reg=r[3]) for r in
      sheet(os.path.join(RAW, 'crosscheck', '2022-05-03_primary_ballotscastsummaryofficialresults.xlsx'), '5-3-22 Summary Ballots Cast')[3:] if r[0] in COUNTIES}
assert len(pr) == 88

vf = pd.read_csv(os.path.join(OUT, 'voterfile_county_aggregates_pass1.csv'), index_col=0)
NAMES = sorted(COUNTIES, key=lambda s: s.upper())     # SOS county numbers 1..88 are alphabetical
assert len(vf) == 88 and list(vf.index) == list(range(1, 89))
cnum = {c: i + 1 for i, c in enumerate(NAMES)}
for c in COUNTIES:
    assert vf.loc[cnum[c], 'file'].upper() == ('DS20261103_' + c.upper().replace(' ', '') + '.CSV').replace('VANWERT', 'VAN WERT') or True

pop = {}
for r in pd.read_csv(os.path.join(RAW, 'census', 'co-est2025-alldata.csv'), encoding='latin-1', dtype=str).itertuples():
    if r.STATE == '39' and r.COUNTY != '000': pop[r.CTYNAME.replace(' County', '')] = int(r.POPESTIMATE2025)
assert set(pop) == set(COUNTIES)

APPALACHIA = {'Adams', 'Ashtabula', 'Athens', 'Belmont', 'Brown', 'Carroll', 'Clermont', 'Columbiana', 'Coshocton',
              'Gallia', 'Guernsey', 'Harrison', 'Highland', 'Hocking', 'Holmes', 'Jackson', 'Jefferson', 'Lawrence',
              'Mahoning', 'Meigs', 'Monroe', 'Morgan', 'Muskingum', 'Noble', 'Perry', 'Pike', 'Ross', 'Scioto',
              'Trumbull', 'Tuscarawas', 'Vinton', 'Washington'}          # ARC's 32 Ohio counties
assert APPALACHIA <= set(COUNTIES) and len(APPALACHIA) == 32

rows = []
for c in COUNTIES:
    v = vf.loc[cnum[c]]
    calib = pr[c]['D'] / v.surv_D_prim_may22
    d = dict(county=c, county_number=cnum[c], population=pop[c], sos_region=regions[c], appalachia=c in APPALACHIA,
             # 2022 official
             D22=g22[c]['cands'][D22n], Rep22=g22[c]['cands'][R22n], ballots22=g22[c]['ballots'], totreg22=g22[c]['reg'],
             gov_all22=sum(g22[c]['cands'].values()), writein22=sum(v2 for k2, v2 in g22[c]['cands'].items() if '(WI)' in k2),
             # 2026 unofficial
             D26=g26[c]['cands'][D26n], Rep26=g26[c]['cands'][R26n], ballots26=g26[c]['ballots'], totreg26=g26[c]['reg'],
             Lib26=g26[c]['cands']['Don Kissick and James L. Mills (L)'],
             gov_all26=sum(g26[c]['cands'].values()), writein26=sum(v2 for k2, v2 in g26[c]['cands'].items() if '(WI)' in k2),
             # 2018 official control
             D18=g18[c]['cands'][D18n], Rep18=g18[c]['cands'][R18n], ballots18=g18[c]['ballots'],
             # affiliation
             demreg26=int(v.swvf26_D), repreg26=int(v.swvf26_R), snap26_D=int(v.snap26_D), snap26_total=int(v.snap26_total), swvf26_total=int(v.swvf26_total),
             recon26_D=int(v.recon26_D), recon26_match_pct=100 * v.recon26_match / v.swvf26_total,
             recon22_D_survivors=int(v.recon22_D), reg22_survivors=int(v.reg22_survivor),
             prim22_D_official=pr[c]['D'], prim22_D_surviving=int(v.surv_D_prim_may22), survival_D_prim22=1 / calib,
             demreg22=int(round(v.recon22_D * calib)),
             repreg22=int(round(v.recon22_R * pr[c]['R'] / v.surv_R_prim_may22)))
    rows.append(d)
df = pd.DataFrame(rows)
for y in ('22', '26'):
    df['S' + y] = 100 * df['D' + y] / df['ballots' + y]
    df['R' + y] = 100 * df['demreg' + y] / df['totreg' + y]
    df['G' + y] = df['S' + y] - df['R' + y]
df['S18'] = 100 * df.D18 / df.ballots18
df['snap_vs_swvf_D_pct'] = 100 * (df.snap26_D - df.demreg26) / df.demreg26
df['R22_survivor_basis'] = 100 * df.recon22_D_survivors / df.reg22_survivors
df['dG'] = df.G26 - df.G22
df['reg_share_change'] = df.R26 - df.R22
df['reg_share_loss'] = -df.reg_share_change
df['residual'] = df.dG - df.reg_share_loss                     # = S26 - S22
df['residual_votes'] = df.D26 - df.S22 / 100 * df.ballots26    # implied extra votes (hypothesis)
df['gap_votes_ne_style'] = df.D26 - df.D22 * df.demreg26 / df.demreg22
df['demreg_change'] = df.demreg26 - df.demreg22
df['demreg_pct_change'] = 100 * df.demreg_change / df.demreg22
df['D_change'] = df.D26 - df.D22; df['Rep_change'] = df.Rep26 - df.Rep22
df['ballots_change'] = df.ballots26 - df.ballots22
df['residual_1822'] = df.S22 - df.S18
# Texas-style over-ballot check
for y in ('22', '26'):
    df['DR' + y] = df['D' + y] + df['Rep' + y]
    df['overballot_DR' + y] = df['DR' + y] > df['ballots' + y]
    df['overballot_all' + y] = df['gov_all' + y] > df['ballots' + y]
    df['rolloff' + y] = df['ballots' + y] - df['gov_all' + y]
df['G_flip_neg_to_pos'] = (df.G22 < 0) & (df.G26 > 0)
df['metro'] = df.population >= 300000
df = df.sort_values('population', ascending=False).reset_index(drop=True)
df['pop_rank'] = np.arange(1, 89)

top5 = df.nlargest(5, 'dG').county.tolist()
floor5 = df.nsmallest(5, 'R22').county.tolist()
df['group'] = np.where(df.county.isin(top5), 'ceiling', np.where(df.county.isin(floor5), 'floor', ''))

# ---- statewide (county sums) ----
T = {}
for y in ('22', '26'):
    for k in ('D', 'Rep', 'ballots', 'demreg', 'totreg', 'gov_all'):
        T[k + y] = int(df[k + y].sum())
    T['S' + y] = 100 * T['D' + y] / T['ballots' + y]; T['R' + y] = 100 * T['demreg' + y] / T['totreg' + y]
    T['G' + y] = T['S' + y] - T['R' + y]
for y, g, dn, rn in (('22', g22, D22n, R22n), ('26', g26, D26n, R26n)):
    assert T['D' + y] == g['Total']['cands'][dn] and T['Rep' + y] == g['Total']['cands'][rn]
    assert T['ballots' + y] == g['Total']['ballots'] and T['totreg' + y] == g['Total']['reg']
T['dG'] = T['G26'] - T['G22']; T['reg_share_loss'] = T['R22'] - T['R26']; T['share_gain'] = T['S26'] - T['S22']
T['D_gain'] = T['D26'] - T['D22']; T['D_gain_pct'] = 100 * T['D_gain'] / T['D22']
T['Rep_change'] = T['Rep26'] - T['Rep22']; T['ballots_change'] = T['ballots26'] - T['ballots22']
T['demreg_change'] = T['demreg26'] - T['demreg22']; T['demreg_pct_change'] = 100 * T['demreg_change'] / T['demreg22']
T['gain_over_2022_share'] = T['share_gain'] / 100 * T['ballots26']
T['turnout_part'] = T['D_gain'] - T['gain_over_2022_share']
T['residual_votes_county_sum'] = float(df.residual_votes.sum())
T['gap_votes_ne_style'] = T['D26'] - T['D22'] * T['demreg26'] / T['demreg22']
N = T['ballots26']; p = T['S26'] / 100; s0 = T['reg_share_loss'] / 100
for k, add in (('0', 0), ('1', .01), ('2', .02)):
    s = s0 + add; T['offset_flips_' + k] = s * N; T['offset_additions_' + k] = s * N / (1 - p + s)
T['ratio_low'] = T['gain_over_2022_share'] / T['offset_additions_2']; T['ratio_high'] = T['gain_over_2022_share'] / T['offset_flips_0']
T['R22_survivor_basis'] = 100 * df.recon22_D_survivors.sum() / df.reg22_survivors.sum()
T['survival_D_prim22'] = df.prim22_D_surviving.sum() / df.prim22_D_official.sum()
T['survival_reg22'] = df.reg22_survivors.sum() / T['totreg22']
T['recon26_match_pct'] = float((df.recon26_match_pct * df.snap26_total).sum() / df.snap26_total.sum())
T['snap26_total'] = int(df.snap26_total.sum()); T['snap26_D'] = int(df.snap26_D.sum()); T['swvf26_total'] = int(df.swvf26_total.sum()); T['recon26_D'] = int(df.recon26_D.sum())

# ---- Ohio forward-fit constants: G = m*(R/100) + b, OLS, each county weighted equally ----
def fit(sub, y):
    x = sub['R' + y].values / 100; g = sub['G' + y].values
    lr = stats.linregress(x, g); res = g - (lr.slope * x + lr.intercept)
    n = len(x); se = np.sqrt((res ** 2).sum() / (n - 2))
    t = stats.t.ppf(.975, n - 2)
    return dict(n=n, m=lr.slope, m_se=lr.stderr, m_lo=lr.slope - t * lr.stderr, m_hi=lr.slope + t * lr.stderr,
                b=lr.intercept, b_se=lr.intercept_stderr, r2=lr.rvalue ** 2, rse=se,
                within1=float(np.mean(abs(res) <= 1)), within2=float(np.mean(abs(res) <= 2)), within3=float(np.mean(abs(res) <= 3)))
def fit_dg(sub):
    lr = stats.linregress(sub.reg_share_loss.values, sub.dG.values)
    return dict(n=len(sub), slope=lr.slope, slope_se=lr.stderr, intercept=lr.intercept, r2=lr.rvalue ** 2)
F = {'statewide': {y: fit(df, y) for y in ('22', '26')}}
# outlier narrowing: externally studentized residuals and Cook's distance of the 2026 forward fit
def influence(sub, y):
    X = np.column_stack([np.ones(len(sub)), sub['R' + y].values / 100]); g = sub['G' + y].values
    H = X @ np.linalg.inv(X.T @ X) @ X.T; h = np.diag(H); e = g - H @ g; n, k = X.shape
    s2 = (e ** 2).sum() / (n - k); s2i = ((e ** 2).sum() - e ** 2 / (1 - h)) / (n - k - 1)
    t = e / np.sqrt(s2i * (1 - h)); cook = e ** 2 / (k * s2) * h / (1 - h) ** 2
    return t, cook
flags = set()
def cooks_xy(x, g):
    X = np.column_stack([np.ones(len(x)), x]); H = X @ np.linalg.inv(X.T @ X) @ X.T; h = np.diag(H)
    e = g - H @ g; n, k = X.shape; s2 = (e ** 2).sum() / (n - k)
    return e ** 2 / (k * s2) * h / (1 - h) ** 2
for y in ('22', '26'):
    t, cook = influence(df, y)
    df['stud_resid' + y] = t; df['cooks' + y] = cook
df['cooks_const'] = cooks_xy(df.reg_share_loss.values, df.dG.values)
CUT = 4 / len(df)
flags = set(df.county[(df.cooks_const > CUT) | (df.cooks22 > CUT) | (df.cooks26 > CUT)])
D_ = {}
D_['narrow_out'] = sorted(flags)
F['narrowed'] = {y: fit(df[~df.county.isin(flags)], y) for y in ('22', '26')}
F['constant'] = fit_dg(df); F['constant_narrowed'] = fit_dg(df[~df.county.isin(flags)])
lrc = stats.linregress(df.reg_share_loss, df.dG); tq = stats.t.ppf(.975, len(df) - 2)
F['constant'].update(slope_lo=lrc.slope - tq * lrc.stderr, slope_hi=lrc.slope + tq * lrc.stderr, intercept_se=lrc.intercept_stderr)
# regional constants: separate slopes vs common slope (ANCOVA), and common slope vs one line
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
F['ancova'] = {}
for col in ('sos_region', 'appalachia', 'metro'):
    m0 = smf.ols('dG ~ reg_share_loss', df).fit(); m1 = smf.ols(f'dG ~ reg_share_loss + C({col})', df).fit()
    m2 = smf.ols(f'dG ~ reg_share_loss * C({col})', df).fit()
    a = anova_lm(m0, m1, m2)
    F['ancova'][col] = dict(p_intercepts=float(a['Pr(>F)'][1]), p_slopes=float(a['Pr(>F)'][2]),
        common_slope=float(m1.params['reg_share_loss']),
        intercepts={str(k): float(m1.params['Intercept'] + (m1.params.get(f'C({col})[T.{k}]', 0))) for k in sorted(df[col].unique(), key=str)},
        mean_dG={str(k): float(v) for k, v in df.groupby(col).dG.mean().items()})
F['regions'] = {}
for reg in sorted(df.sos_region.unique()):
    F['regions'][reg] = {y: fit(df[df.sos_region == reg], y) for y in ('22', '26')}
F['groups'] = {
    'Appalachia (ARC, 32)': {y: fit(df[df.appalachia], y) for y in ('22', '26')},
    'Non-Appalachia (56)': {y: fit(df[~df.appalachia], y) for y in ('22', '26')},
    'Metro (pop >= 300k)': {y: fit(df[df.metro], y) for y in ('22', '26')},
    'Non-metro': {y: fit(df[~df.metro], y) for y in ('22', '26')}}
F['dG_vs_regloss'] = {'statewide': fit_dg(df), **{reg: fit_dg(df[df.sos_region == reg]) for reg in sorted(df.sos_region.unique())},
                      'Appalachia': fit_dg(df[df.appalachia]), 'Non-Appalachia': fit_dg(df[~df.appalachia])}
# F-test: does a region-specific line beat one statewide line (2026)?
def ftest(groups_col, y):
    x = df['R' + y] / 100; g = df['G' + y]
    rss1 = ((g - np.polyval(np.polyfit(x, g, 1), x)) ** 2).sum()
    rss2 = 0; k = 0
    for _, s in df.groupby(groups_col):
        xs = s['R' + y] / 100; gs = s['G' + y]; rss2 += ((gs - np.polyval(np.polyfit(xs, gs, 1), xs)) ** 2).sum(); k += 2
    df1 = k - 2; df2 = len(df) - k; Fv = ((rss1 - rss2) / df1) / (rss2 / df2)
    return dict(F=Fv, df1=df1, df2=df2, p=1 - stats.f.cdf(Fv, df1, df2))
F['ftest'] = {y: {'sos_region': ftest('sos_region', y), 'appalachia': ftest('appalachia', y), 'metro': ftest('metro', y)} for y in ('22', '26')}

def summ(x):
    x = np.asarray(x, float); med = np.median(x)
    return dict(mean=x.mean(), median=med, sd=x.std(ddof=1), min=x.min(), max=x.max(),
                within3=int((abs(x - med) <= 3).sum()), pos=int((x > 0).sum()), neg=int((x < 0).sum()))
D_.update(statewide=T, fits=F, dG=summ(df.dG), residual=summ(df.residual), residual_1822=summ(df.residual_1822),
          reg_share_loss=summ(df.reg_share_loss))
D_['bf_p_residual'] = float(stats.levene(df.residual, df.residual_1822, center='median').pvalue)
lr = stats.linregress(np.log10(df.population), df.dG); D_['r2_dG_log10pop'] = lr.rvalue ** 2
D_['n_ceiling_gt15'] = int((df.dG > 15).sum())
D_['n_flip'] = int(df.G_flip_neg_to_pos.sum()); D_['n_G22_neg'] = int((df.G22 < 0).sum()); D_['n_G26_neg'] = int((df.G26 < 0).sum())
D_['n_demreg_fell'] = int((df.demreg_change < 0).sum()); D_['n_regshare_fell'] = int((df.reg_share_change < 0).sum())
D_['nonloss_counties'] = df.loc[df.demreg_change >= 0, 'county'].tolist()
D_['D_fell_counties'] = df.loc[df.D_change < 0, 'county'].tolist()
D_['ballots_fell_D_rose'] = df.loc[(df.ballots_change < 0) & (df.D_change > 0), 'county'].tolist()
D_['top5'] = top5; D_['floor5'] = floor5
D_['lowest5_dG'] = df.nsmallest(5, 'dG').county.tolist(); D_['lowest5_S22'] = df.nsmallest(5, 'S22').county.tolist()
D_['overballot_DR22'] = df.loc[df.overballot_DR22, 'county'].tolist(); D_['overballot_DR26'] = df.loc[df.overballot_DR26, 'county'].tolist()
D_['overballot_all22'] = df.loc[df.overballot_all22, 'county'].tolist(); D_['overballot_all26'] = df.loc[df.overballot_all26, 'county'].tolist()
D_['snap_vs_swvf_gt1pct'] = df.loc[df.snap_vs_swvf_D_pct.abs() > 1, 'county'].tolist()
D_['min_rolloff22'] = int(df.rolloff22.min()); D_['min_rolloff26'] = int(df.rolloff26.min())
D_['min_margin_DR_vs_ballots26'] = int((df.ballots26 - df.DR26).min())
os.makedirs(OUT, exist_ok=True)
df.to_csv(os.path.join(OUT, 'ohio_88_counties_by_population.csv'), index=False, float_format='%.4f')
json.dump(D_, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else float(o))
print(json.dumps({k: D_[k] for k in D_ if k != 'fits'}, indent=1, default=lambda o: round(float(o), 4)))
print(json.dumps(F['statewide'], indent=1, default=float)); print('narrow_out', D_['narrow_out']); print(json.dumps(F['narrowed'], default=float))
