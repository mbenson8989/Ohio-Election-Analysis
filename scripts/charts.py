"""Charts for the Ohio wiki (PNG, repo root). Same chart set and style as the Pennsylvania / Iowa wikis."""
import os, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = ROOT + '/'
t = pd.read_csv(ROOT + '/data/ohio_88_counties_by_population.csv'); S = json.load(open(ROOT + '/data/summary.json'))
n = len(t); x = np.arange(n)
UN = ('2026* figures UNOFFICIAL (Ohio SOS unofficial canvass, not certified). Dem affiliation: SOS voter files (2022 reconstructed from '
      'voter history, R.C. 3513.19). Census V2025 population (sort order).')
fl, ce = t.loc[t.dG.idxmin(), 'county'], t.loc[t.dG.idxmax(), 'county']
top5, floor5 = S['top5'], S['floor5']
cols = {'Northeast': '#1f77b4', 'Northwest': '#9467bd', 'Central': '#2ca02c', 'West': '#8c564b', 'Southwest': '#e377c2', 'Southeast': '#7f7f7f'}
def foot(fig): fig.text(0.01, 0.005, UN, fontsize=7, color='#555')
def save(fig, name, dpi=120): foot(fig); fig.tight_layout(rect=(0, .025, 1, 1)); fig.savefig(O + name, dpi=dpi); plt.close(fig)
names = {}
# 1 slope chart
fig, ax = plt.subplots(figsize=(9, 12))
for r in t.itertuples():
    hi = r.county in top5 or r.county in floor5
    c = '#d95f02' if r.county in top5 else '#1b9e77' if r.county in floor5 else cols[r.sos_region]
    ax.plot([0, 1], [r.G22, r.G26], color=c, alpha=.85 if hi else .4, lw=2.2 if hi else 1)
    if hi or r.population > 500000: ax.text(1.02, r.G26, f'{r.county} ({r.dG:+.2f}*)', fontsize=7, va='center')
ax.set_xticks([0, 1]); ax.set_xticklabels(['G 2022 (official)', 'G 2026* (unofficial)']); ax.set_xlim(-.1, 1.5); ax.axhline(0, color='k', lw=.5)
ax.set_ylabel('G = Dem share of ballots − Dem affiliation share (points)')
ax.set_title(f'Ohio: G 2022 → G 2026*, all 88 counties\nG rose in {S["dG"]["pos"]} of 88; lowest ΔG {fl} {t.dG.min():+.2f}*, highest {ce} {t.dG.max():+.2f}*')
h = [Patch(color=c, label=k) for k, c in cols.items()] + [Patch(color='#d95f02', label='Ceiling (top 5 ΔG)'), Patch(color='#1b9e77', label='Floor (5 lowest 2022 Dem affiliation share)')]
ax.legend(handles=h, fontsize=7, loc='lower left'); names['slope'] = 'OH_Slope_G2022_to_G2026_County_Slope_Chart.png'; save(fig, names['slope'], 130)
# 2 stacked share by population
fig, ax = plt.subplots(figsize=(18, 6.5)); dS = t.S26 - t.S22
ax.bar(x, t.S22, color='#4c78a8', label='2022 Democratic share of ballots (official)')
ax.bar(x, dS.clip(lower=0), bottom=t.S22, color='#f58518', label='2022 → 2026* gain')
ax.set_xticks(x); ax.set_xticklabels(t.county, rotation=90, fontsize=7); ax.set_ylabel('% of ballots cast')
ax.set_title('Ohio governor: 2022 Democratic share of ballots + 2026* change, counties largest → smallest population'); ax.legend(fontsize=8)
names['stacked'] = 'OH_governor_stacked_share_by_population.png'; save(fig, names['stacked'])
# 3 vote-share change above the line, registration-share loss below
fig, ax = plt.subplots(figsize=(18, 6.5))
ax.bar(x, dS, color='#f58518', label='Vote-share change 2022 → 2026* (pts)')
ax.bar(x, t.reg_share_change, color='#4c78a8', label='Dem affiliation-share change (pts, negative = loss)')
ax.plot(x, t.dG, 'k.', label='ΔG* (= vote-share change + affiliation-share loss)'); ax.axhline(0, color='k', lw=.6)
ax.set_xticks(x); ax.set_xticklabels(t.county, rotation=90, fontsize=7); ax.set_ylabel('points')
ax.set_title('Ohio: vote-share change above the line, Democratic affiliation-share change below, population order'); ax.legend(fontsize=8)
names['regloss'] = 'OH_governor_stacked_share_with_Dem_registration_loss_by_population.png'; save(fig, names['regloss'])
# 4 dG population order
fig, ax = plt.subplots(figsize=(18, 6.5))
c = ['#1b9e77' if v == fl else '#d95f02' if v == ce else cols[r] for v, r in zip(t.county, t.sos_region)]
ax.bar(x, t.dG, color=c); ax.axhline(t.dG.median(), color='k', ls='--', lw=.8, label=f'median {t.dG.median():+.2f}*')
ax.axhline(15, color='r', ls=':', lw=.8, label='ΔG = 15')
ax.set_xticks(x); ax.set_xticklabels(t.county, rotation=90, fontsize=7); ax.set_ylabel('ΔG* (points)')
ax.set_title(f'Ohio ΔG*, all 88 counties largest → smallest population. Lowest: {fl} {t.dG.min():+.2f}*; highest: {ce} {t.dG.max():+.2f}*')
h = [Patch(color=cc, label=k) for k, cc in cols.items()] + [Patch(color='#1b9e77', label=f'Lowest ΔG {fl}'), Patch(color='#d95f02', label=f'Highest ΔG {ce}')]
ax.legend(handles=h + ax.get_legend_handles_labels()[0], fontsize=7)
names['dGpop'] = f'OH_deltaG_by_county_population_order_-_floor_{fl}_ceiling_{ce}.png'; save(fig, names['dGpop'])
# 5 constant scatter
k = S['fits']['constant']; fig, ax = plt.subplots(figsize=(10, 7))
for rg, d in t.groupby('sos_region'):
    ax.scatter(d.reg_share_loss, d.dG, color=cols[rg], label=rg, s=np.clip(np.sqrt(d.population) / 8, 10, 220), alpha=.75, edgecolor='k', lw=.3)
xx = np.linspace(t.reg_share_loss.min() - .2, t.reg_share_loss.max() + .2, 10)
ax.plot(xx, k['intercept'] + k['slope'] * xx, 'k-', label=f'Ohio constant: ΔG = {k["intercept"]:+.2f} + {k["slope"]:.2f} × drop (R² {k["r2"]:.2f}, n=88)')
for r in t.itertuples():
    if r.county in S['narrow_out'] or r.county in (fl, ce) or r.population > 600000:
        ax.annotate(r.county, (r.reg_share_loss, r.dG), fontsize=7, xytext=(3, 3), textcoords='offset points')
ax.set_xlabel('Democratic affiliation-share drop 2022 → 2026 (points)'); ax.set_ylabel('ΔG* (points)')
ax.set_title('Ohio reverse-factoring constant (Ohio data only)\nmarker size ~ population; labeled: narrowed-out, highest/lowest ΔG, largest counties')
ax.legend(fontsize=7); names['const'] = 'OH_DeltaG_vs_Registration_Share_Drop_OH_Constant.png'; save(fig, names['const'], 130)
# 6 forward fit 2022 and 2026
fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
for ax, y, lab in ((axs[0], '22', '2022 (official)'), (axs[1], '26', '2026* (unofficial)')):
    f = S['fits']['statewide'][y]
    for rg, d in t.groupby('sos_region'): ax.scatter(d['R' + y], d['G' + y], color=cols[rg], s=18, label=rg)
    xx = np.linspace(t['R' + y].min(), t['R' + y].max(), 10)
    ax.plot(xx, f['m'] * xx / 100 + f['b'], 'k-', label=f'G = {f["m"]:.1f} × R/100 {f["b"]:+.2f} (R² {f["r2"]:.2f})')
    ax.set_xlabel('R: Dem affiliation share (%)'); ax.set_title(f'Forward fit {lab}'); ax.legend(fontsize=7)
axs[0].set_ylabel('G (points)'); names['fwd'] = 'OH_Forward_Fit_G_on_R_2022_2026.png'; save(fig, names['fwd'], 130)
# 7 ceiling & floor bars
sel = t[t.county.isin(top5 + floor5)].sort_values('population', ascending=False)
fig, ax = plt.subplots(figsize=(12, 5)); ax.bar(sel.county, sel.dG, color=['#d95f02' if v in top5 else '#1b9e77' for v in sel.county])
for i, v in enumerate(sel.dG): ax.text(i, v + .2, f'{v:+.2f}*', ha='center', fontsize=8)
ax.set_ylabel('ΔG* (points)'); ax.set_title('Ohio ceiling (top 5 ΔG, orange) and floor (5 lowest 2022 Dem affiliation share, green) counties, population order')
plt.xticks(rotation=30); names['cf'] = 'OH_Ceiling_and_Floor_Counties_DeltaG_by_Population.png'; save(fig, names['cf'], 130)
# 8 Texas-style check
fig, ax = plt.subplots(figsize=(18, 6.5))
ax.plot(x, 100 * t.DR22 / t.ballots22, 'o-', ms=3, label='2022 (official): (D + R) ÷ ballots')
ax.plot(x, 100 * t.DR26 / t.ballots26, 's-', ms=3, label='2026* (unofficial): (D + R) ÷ ballots')
ax.axhline(100, color='r', lw=1, label='100% line (D + R = ballots cast)')
for r in t[t.overballot_DR26 | t.overballot_DR22].itertuples():
    ax.annotate(f'{r.county} 2026*: {r.DR26:,} D+R vs {r.ballots26:,} ballots', (r.pop_rank - 1, 100 * r.DR26 / r.ballots26), fontsize=8, color='r', xytext=(-160, 8), textcoords='offset points')
ax.set_xticks(x); ax.set_xticklabels(t.county, rotation=90, fontsize=7); ax.set_ylabel('% of ballots cast')
ax.set_title(f'Texas-style check: Democratic + Republican governor votes vs ballots cast. Over the line: 2022 {len(S["overballot_DR22"])}, 2026* {len(S["overballot_DR26"])} ({", ".join(S["overballot_DR26"]) or "none"})')
ax.legend(fontsize=8); names['tx'] = 'OH_over_ballot_check_dem_plus_rep_vs_ballots.png'; save(fig, names['tx'])
# 9 residual strip, 2022->2026 vs 2018->2022 control
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.scatter(t.residual, np.zeros(n) + 1, alpha=.6, label=f'2022 → 2026* (SD {S["residual"]["sd"]:.2f})')
ax.scatter(t.residual_1822, np.zeros(n), alpha=.6, color='#888', label=f'2018 → 2022 control, official both years (SD {S["residual_1822"]["sd"]:.2f})')
ax.set_yticks([0, 1]); ax.set_yticklabels(['2018 → 2022', '2022 → 2026*']); ax.axvline(0, color='k', lw=.5)
ax.set_xlabel('Residual = vote-share change (points)'); ax.set_title(f'Ohio residual spread vs control cycle (Brown-Forsythe p = {S["bf_p_residual"]:.2f})'); ax.legend(fontsize=8)
names['strip'] = 'OH_Residual_Strip_2022_2026_vs_2018_2022_Control.png'; save(fig, names['strip'], 130)
json.dump(names, open(ROOT + '/data/chart_files.json', 'w'), indent=1); print(names)
