"""Write the 5 Ohio wiki pages + _Sidebar to ../Ohio.wiki/ (the wiki git clone) from data/ (all numbers from the verified table and summary).
Markdown rules used so pages render cleanly on GitHub: ASCII-only headings (stable anchors), every table built by one
helper (header + separator + rows with equal column counts), the 2026 marker written as \\* (never a bare *),
no raw HTML, absolute links between pages."""
import os, json, re, datetime
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.environ.get('WIKI_DIR', os.path.join(os.path.dirname(ROOT), 'Ohio.wiki')); os.makedirs(W, exist_ok=True)
t = pd.read_csv(os.path.join(ROOT, 'data', 'ohio_88_counties_by_population.csv'))
S = json.load(open(os.path.join(ROOT, 'data', 'summary.json'))); T = S['statewide']; F = S['fits']
P1 = json.load(open(os.path.join(ROOT, 'verification', 'pass1_report.json'))); P2 = json.load(open(os.path.join(ROOT, 'verification', 'pass2_report.json')))
CH = json.load(open(os.path.join(ROOT, 'data', 'chart_files.json')))
REPO = 'https://github.com/mbenson8989/Ohio-Election-Analysis'; WIKI = REPO + '/wiki'
RAWURL = 'https://raw.githubusercontent.com/mbenson8989/Ohio-Election-Analysis/main/'
CEDAR = 'https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki/Cedar-Audit'
NEWIKI = 'https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki'
BUILT = os.environ.get('BUILT', datetime.datetime.now().strftime('%b %d %Y %I:%M %p CST'))
A = '\\*'                                       # the 2026 "unofficial" marker, escaped for markdown
L = lambda page, text=None: f'[{text or page.replace("-", " ")}]({WIKI}/{page})'
PAGES = [('Home', 'Home'), ('Reverse-Math', 'Reverse Math'), ('Locked-Ohio-Formula', 'Locked Ohio Formula'),
         ('Floor-and-Ceiling', 'Floor and Ceiling'), ('Graphs', 'Graphs'), ('Ohio-County-PDF-Information', 'Ohio County PDF Information')]
PDFNAME = 'Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf'
PDFRAW = REPO + '/raw/main/' + PDFNAME
def i(v): return f'{int(round(v)):,}'
def sg(v, d=2): return f'{v:+,.{d}f}'
def pc(v, d=2): return f'{v:.{d}f}%'
def table(hdr, rows):
    for r in rows: assert len(r) == len(hdr), (hdr, r)
    cell = lambda x: str(x).replace('|', '\\|').replace('\n', ' ')
    out = ['| ' + ' | '.join(cell(h) for h in hdr) + ' |', '|' + '|'.join('---' for _ in hdr) + '|']
    out += ['| ' + ' | '.join(cell(x) for x in r) + ' |' for r in rows]
    return '\n'.join(out)
def slug(h): return re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-')
def toc(heads): return '\n'.join(f'- [{h}](#{slug(h)})' for h in heads)
def img(key, alt): return f'![{alt}]({RAWURL}{CH[key]})'
def related(cur):
    return '---\n**Related:** ' + ' · '.join(L(p, n) for p, n in PAGES if p != cur) + f' · [Cedar County Audit (Nebraska)]({CEDAR})'
row = lambda c: t[t.county == c].iloc[0]
BANNER = (f'> **{A}2026 figures are UNOFFICIAL.** They come from the Ohio Secretary of State (SOS) "November 3, 2026 General Unofficial Canvass" '
          f'file on liveresults.ohiosos.gov, downloaded Nov 19, 2026 11:53 AM CST. The SOS states results are unofficial until it certifies them; it has not. '
          f'2022 figures are the SOS official canvass. Governor race. **Ohio has no party registration:** the "registration" share on these pages is the '
          f'Democratic **party-affiliation** share from the SOS voter files (affiliation = the party whose primary ballot a voter last took, R.C. 3513.19); '
          f'the 2022 figure is reconstructed from SOS voter history ([details]({WIKI}/Home#registration-data-source-and-caveat)). Votes are votes for the '
          f'Democratic candidate, not a count of affiliated Democrats who voted. These pages measure a pattern; they make no claim about intent, fraud or cause.')
k = F['constant']; kn = F['constant_narrowed']; f22 = F['statewide']['22']; f26 = F['statewide']['26']; n22 = F['narrowed']['22']; n26 = F['narrowed']['26']
anc = F['ancova']; NO = S['narrow_out']
top5, floor5, low5 = S['top5'], S['floor5'], S['lowest5_dG']
fl_c = t.loc[t.dG.idxmin()]; ce_c = t.loc[t.dG.idxmax()]
wy = row('Wyandot')
pages = {}

# ------------------------------------------------------------------ Home
heads = ['Pages', 'Statewide at a glance', 'Key findings', 'Registration data source and caveat', 'Verification', 'Sources']
h = [f'# Ohio 2022 vs 2026 Governor Race: Delta-G Method', '', f'**Version 1, built {BUILT}**', '', BANNER, '',
     f'Method developed by Morissa Benson (CD3 Vice Chair, Nebraska GOP). It began with her [Cedar County Audit]({CEDAR}) on the '
     f'[Nebraska Election Analysis wiki]({NEWIKI}): a small county where Democratic governor votes rose while Democratic registration fell. '
     f'This wiki applies the same county-by-county arithmetic to all 88 Ohio counties using Ohio Secretary of State data only. '
     f'The Ohio constant is computed from Ohio data only; no other state\'s constant is reused.', '',
     '## Contents', '', toc(heads), '', '## Pages', '',
     f'1. [Cedar County Audit]({CEDAR}) (Nebraska wiki): where the method began',
     f'2. {L("Reverse-Math", "Reverse Math")}: statewide, the reverse-factoring step, the Ohio constant, regional constants, then all 88 counties (largest to smallest population)',
     f'3. {L("Locked-Ohio-Formula", "Locked Ohio Formula")}: the equation, how Ohio party affiliation is counted, a blank fill-in template and a worked example',
     f'4. {L("Floor-and-Ceiling", "Floor and Ceiling")}: floor and ceiling counties, the Texas-style over-ballot check, counties to narrow out',
     f'5. {L("Graphs")}: slope chart, stacked bars, Delta-G by population, constant scatter, forward fits, ceiling/floor bars, over-ballot check, control cycle',
     f'6. {L("Ohio-County-PDF-Information", "Ohio County PDF Information")}: downloadable 88-county PDF table (Democratic affiliation, Democratic governor votes and total ballots, 2022 vs 2026{A}) and what each column means', '',
     '## Statewide at a glance', '',
     table(['Measure', '2022 (official)', f'2026{A} (unofficial)', 'Change'], [
        ['Democratic-affiliated voters (SOS voter files; 2022 reconstructed)', i(T['demreg22']), i(T['demreg26']), f'{i(T["demreg_change"])} ({T["demreg_pct_change"]:+.1f}%)'],
        ['Registered voters (SOS canvass)', i(T['totreg22']), i(T['totreg26']), i(T['totreg26'] - T['totreg22'])],
        ['Democratic governor votes (Whaley 2022, Acton 2026)', i(T['D22']), i(T['D26']) + A, f'{sg(T["D_gain"], 0)}{A} ({T["D_gain_pct"]:+.1f}%)'],
        ['Republican governor votes (DeWine 2022, Ramaswamy 2026)', i(T['Rep22']), i(T['Rep26']) + A, sg(T['Rep_change'], 0) + A],
        ['Total ballots cast (SOS "Ballots Counted")', i(T['ballots22']), i(T['ballots26']) + A, sg(T['ballots_change'], 0) + A],
        ['**S** = Dem votes / ballots cast', pc(T['S22']), pc(T['S26']) + A, sg(T['share_gain']) + A],
        ['**R** = Dem affiliation share of registered voters', pc(T['R22']), pc(T['R26']), sg(-T['reg_share_loss'])],
        ['**G** = S - R', sg(T['G22']), sg(T['G26']) + A, f'**Delta-G = {sg(T["dG"])}{A}**']]), '',
     '## Key findings', '',
     f'- **Delta-G is positive in all 88 counties** ({fl_c.county} {sg(fl_c.dG)}{A} lowest, {ce_c.county} {sg(ce_c.dG)}{A} highest; median {sg(S["dG"]["median"])}{A}, mean {sg(S["dG"]["mean"])}{A}). {S["dG"]["within3"]} of 88 counties are within 3 points of the median.',
     f'- Democratic affiliation **share** fell in {S["n_regshare_fell"]} counties and the Democratic-affiliated **count** fell in {S["n_demreg_fell"]}. The {len(S["nonloss_counties"])} non-loss counties are {", ".join(S["nonloss_counties"])}.',
     f'- **Residual after the reverse-factoring step** (Delta-G minus the affiliation-share loss = vote-share change): median {sg(S["residual"]["median"])}{A}, positive in all 88. Solved backward, the county residuals add up to **{i(T["residual_votes_county_sum"])}{A} implied extra votes** (hypothesis; see {L("Reverse-Math", "Reverse Math")}).',
     f'- **Ohio constant (Ohio data only):** Delta-G = {sg(k["intercept"])} + {k["slope"]:.2f} x affiliation-share drop (n = 88, slope 95% CI {k["slope_lo"]:.2f} to {k["slope_hi"]:.2f}, R² {k["r2"]:.2f}). With {len(NO)} influential counties narrowed out: Delta-G = {sg(kn["intercept"])} + {kn["slope"]:.2f} x drop (n = {kn["n"]}, R² {kn["r2"]:.2f}).',
     f'- **Forward-fit constants** (G = m x R/100 + b): 2022 m = {f22["m"]:.1f}, b = {sg(f22["b"])} (R² {f22["r2"]:.2f}); 2026{A} m = {f26["m"]:.1f}, b = {sg(f26["b"])} (R² {f26["r2"]:.2f}).',
     f'- **Regional constants:** SOS regions do not share one line (different intercepts p = {anc["sos_region"]["p_intercepts"]:.1e}; different slopes p = {anc["sos_region"]["p_slopes"]:.3f}). Northwest sits highest (common-slope intercept {sg(anc["sos_region"]["intercepts"]["Northwest"])}), Southeast lowest ({sg(anc["sos_region"]["intercepts"]["Southeast"])}). Appalachian counties sit {anc["appalachia"]["intercepts"]["False"] - anc["appalachia"]["intercepts"]["True"]:.2f} points below the rest (p = {anc["appalachia"]["p_intercepts"]:.4f}); large metros (population 300,000+) sit {anc["metro"]["intercepts"]["True"] - anc["metro"]["intercepts"]["False"]:.2f} points above (p = {anc["metro"]["p_intercepts"]:.4f}).',
     f'- **Ceiling (top 5 Delta-G):** ' + ', '.join(f'{c} {sg(row(c).dG)}{A}' for c in top5) + '. **Floor (most Republican baseline, 5 lowest 2022 Democratic affiliation share):** ' + ', '.join(f'{c} {pc(row(c).R22)}' for c in floor5) + '.',
     f'- **Texas-style over-ballot check:** 2022: no county. 2026{A}: **1 county, Wyandot**, where Democratic + Republican governor votes ({i(wy.DR26)}) exceed SOS ballots counted ({i(wy.ballots26)}) by {i(wy.DR26 - wy.ballots26)}; all governor votes exceed ballots by {i(wy.gov_all26 - wy.ballots26)}. Every statewide race in Wyandot exceeds its ballots-counted figure in the unofficial file. See {L("Floor-and-Ceiling", "Floor and Ceiling")}.', '',
     '## Registration data source and caveat', '',
     '**Ohio has no formal party registration.** A voter is affiliated with a party by voting that party\'s primary ballot. Under R.C. 3513.19 and the SOS\'s own definition, a voter is a member of the party whose primary they voted in during the current year or the two preceding calendar years; otherwise they are unaffiliated. The SOS does not publish county party-affiliation totals for either election, so these pages count them from the SOS voter files:', '',
     table(['Year', 'Democratic-affiliated count', 'Source', 'Status'], [
        ['2026', i(T['demreg26']), 'SOS weekly statewide voter file (SWVF, 4 files, "Last Updated 14-NOV-26"), PARTY_AFFILIATION = D', 'Direct SOS field'],
        ['2026 cross-check', i(T['snap26_D']), 'SOS DATA Act daily voter-registration snapshot, Nov 3, 2026 (election day), all 88 county files', f'Within 1% of the SWVF in 83 of 88 counties; not used in the math'],
        ['2022', i(T['demreg22']), 'Reconstructed from the same SWVF voter-history columns with the statutory rule (last party primary ballot, Jan 1 2020 to Nov 8 2022), calibrated for removed voters (below)', 'Derived estimate']]), '',
     f'- **No 2022 voter file is still published.** The SOS posts only the current weekly file, and DATA Act snapshots go back only to Jan 19, 2025. So 2022 affiliation has to be rebuilt from voter history. The rule was tested on 2026: rebuilding 2026 affiliation from history reproduces the SOS PARTY_AFFILIATION field for {T["recon26_match_pct"]:.1f}% of all records.',
     f'- **Survivor calibration.** Voters removed from the rolls after 2022 are not in today\'s file ({100 * (1 - T["survival_reg22"]):.1f}% of 2022 registrants are gone). For each county the rebuilt count is scaled by the SOS official count of May 3, 2022 Democratic primary ballots divided by the number of those voters still in the file (statewide {100 * T["survival_D_prim22"]:.1f}% survive). Uncalibrated, the 2022 share among surviving records would be {pc(T["R22_survivor_basis"])} instead of {pc(T["R22"])}.',
     f'- **Outside check:** for Cuyahoga the calibrated 2022 count is {i(row("Cuyahoga").demreg22)}; the Cuyahoga County Board of Elections voter-control report of Dec 1, 2022 lists 183,502 Democrats ({100 * (row("Cuyahoga").demreg22 / 183502 - 1):+.1f}%).',
     '- The denominator in both years is the SOS canvass "Registered Voters" figure for that election.',
     '- The 2022 affiliation figure is an estimate built from SOS data, not a number the SOS published. Treat 2022 R, G and Delta-G as carrying that uncertainty.', '',
     '## Verification', '',
     f'Every figure for all 88 counties was checked in **two independent passes** against the raw SOS files before anything was published:', '',
     table(['Pass', 'Method', 'Figures checked', 'Matched', 'Mismatched'], [
        ['Pass 1', 'openpyxl on the "Master" sheets, the separate SOS 2022 turnout file, Python csv module over every voter-file record', f'{P1["figures_checked"]:,}', f'{P1["matched"]:,}', str(P1['mismatched'])],
        ['Pass 2', 'separately written: raw OOXML parsing (no spreadsheet library), the SOS NIST 1500-100 XML results feed for 2026 (a second SOS file), DuckDB SQL over the voter files', f'{P2["figures_checked"]:,}', f'{P2["matched"]:,}', str(P2['mismatched'])]]), '',
     '**Discrepancies:** none in the final runs. The first run of Pass 2 reported 2 mismatches, both in a cross-check column not used in any calculation (election-day snapshot Democratic count: Mahoning 24,034 vs 24,073, Clark 8,609 vs 8,610). The cause was Pass 2\'s own CSV reader guessing the wrong escape character; with explicit quoting it matches. The 2026 SOS spreadsheet and the SOS XML feed agree on every county figure. Reports: [verification folder](' + REPO + '/tree/main/verification).', '',
     '## Sources', '',
     table(['Data', 'Source', 'Status'], [
        ['2022 governor results, ballots, registered voters by county', 'SOS "November 8, 2022 General Election Official Canvass", statewide-races-summary.xlsx and 11-8-22-voter-turnout-summary.xlsx (ohiosos.gov, via Wayback id_ copies whose SHA-1 equals the archive digest)', 'Official'],
        ['2026 governor results, ballots, registered voters by county', 'SOS liveresults.ohiosos.gov "November 3, 2026 General Unofficial Canvass" (11032026GenUnTotCanSumm11192026-1753.xlsx) and NIST XML feed, Nov 19 2026 11:53 AM CST', f'**Unofficial**{A}'],
        ['Party affiliation 2026 and 2022', 'SOS statewide voter files SWVF_1_22, SWVF_23_44, SWVF_45_66, SWVF_67_88 (14-NOV-26); SOS DATA Act snapshots DS20261103 (88 counties)', '2026 direct; 2022 derived'],
        ['May 3, 2022 primary ballots by party', 'SOS ballotscastsummaryofficialresults_2022-05-03_primaryelection.xlsx', 'Official'],
        ['2018 control cycle', 'SOS 2018 Official Canvass, as amended by the Miami County BOE', 'Official'],
        ['Population (sort order)', 'U.S. Census Bureau Vintage 2025 county estimates (co-est2025-alldata.csv)', 'Official']]), '',
     f'Data, scripts and both pass reports: [{REPO}]({REPO}).', '', related('Home')]
pages['Home'] = '\n'.join(h)

# ------------------------------------------------------------------ Reverse-Math
cu = row('Cuyahoga')
heads = ['Step 1: the locked gap', 'Step 2: the reverse-factoring step', 'Step 3: Ohio constant', 'Step 4: regional constants', 'Solving backward: implied extra votes', 'What the arithmetic cannot tell you', 'All 88 counties']
def cty_rows(df):
    return [[r.county, i(r.population), r.sos_region, f'{i(r.demreg22)} → {i(r.demreg26)}', f'{r.R22:.2f} → {r.R26:.2f}', f'{i(r.D22)} → {i(r.D26)}{A}',
             f'{i(r.ballots22)} → {i(r.ballots26)}{A}', f'{r.S22:.2f} → {r.S26:.2f}{A}', f'{sg(r.G22)} → {sg(r.G26)}{A}', sg(r.dG) + A, sg(r.residual) + A, sg(r.residual_votes, 0) + A] for r in df.itertuples()]
CT_H = ['County', 'Population', 'SOS region', 'Dem affiliated 2022 → 2026', 'R % 2022 → 2026', 'Dem gov votes 2022 → 2026' + A, 'Ballots 2022 → 2026' + A,
        'S % 2022 → 2026' + A, 'G 2022 → 2026' + A, 'Delta-G' + A, 'Residual' + A, 'Implied extra votes' + A]
reg_rows = []
for rg in sorted(F['regions']):
    d = t[t.sos_region == rg]; r22, r26 = F['regions'][rg]['22'], F['regions'][rg]['26']
    reg_rows.append([rg, str(len(d)), sg(d.dG.mean()) + A, sg(anc['sos_region']['intercepts'][rg]), f'{F["dG_vs_regloss"][rg]["slope"]:.2f}', f'{r22["m"]:.1f} / {r22["b"]:+.2f} / {r22["r2"]:.2f}', f'{r26["m"]:.1f} / {r26["b"]:+.2f} / {r26["r2"]:.2f}'])
for nm, key, sub in (('Appalachia (ARC, 32 counties)', 'Appalachia (ARC, 32)', t[t.appalachia]), ('Rest of Ohio (56)', 'Non-Appalachia (56)', t[~t.appalachia]),
                     ('Metro (population 300,000+)', 'Metro (pop >= 300k)', t[t.metro]), ('Non-metro', 'Non-metro', t[~t.metro])):
    g = F['groups'][key]; dgk = 'Appalachia' if 'ARC' in nm else ('Non-Appalachia' if 'Rest' in nm else None)
    ac = anc['appalachia']['intercepts'][str('ARC' in nm)] if dgk else anc['metro']['intercepts'][str(nm.startswith('Metro'))]
    sl = f'{F["dG_vs_regloss"][dgk]["slope"]:.2f}' if dgk else 'n/a'
    reg_rows.append([nm, str(len(sub)), sg(sub.dG.mean()) + A, sg(ac), sl, f'{g["22"]["m"]:.1f} / {g["22"]["b"]:+.2f} / {g["22"]["r2"]:.2f}', f'{g["26"]["m"]:.1f} / {g["26"]["b"]:+.2f} / {g["26"]["r2"]:.2f}'])
rm = ['# Reverse Math', '', BANNER, '', 'The same arithmetic used in Nebraska\'s [Cedar County Audit](' + CEDAR + '), run on all 88 Ohio counties with the ballots denominator (Democratic governor votes / total ballots cast).', '',
      '## Contents', '', toc(heads), '',
      '## Step 1: the locked gap', '',
      f'G = S - R, where S is the Democratic share of ballots cast and R is the Democratic affiliation share of registered voters. Statewide, G went from {sg(T["G22"])} (2022) to {sg(T["G26"])}{A} (2026), so **Delta-G = {sg(T["dG"])}{A}**.', '',
      table(['Step', 'Statewide value'], [
        ['Democratic share of ballots (S)', f'{pc(T["S22"])} (2022) → {pc(T["S26"])}{A} (2026): **{sg(T["share_gain"])} points{A}**'],
        ['Democratic affiliation share (R)', f'{pc(T["R22"])} → {pc(T["R26"])}: **{sg(-T["reg_share_loss"])} points**'],
        ['Delta-G = vote-share change - affiliation-share change', f'{sg(T["share_gain"])} - ({sg(-T["reg_share_loss"])}) = **{sg(T["dG"])}{A}**']]), '',
      '## Step 2: the reverse-factoring step', '',
      'If Democratic affiliation fell, subtract that expected loss from Delta-G. What is left (the residual) is the vote-share change that the affiliation change does not explain. Worked example, Cuyahoga (the county with the most Democratic-affiliated voters):', '',
      table(['Line', 'Cuyahoga'], [
        ['Democratic share of ballots', f'{cu.S22:.2f}% (2022) → {cu.S26:.2f}%{A} (2026): {sg(cu.S26 - cu.S22)} points{A}'],
        ['Democratic affiliation share', f'{cu.R22:.2f}% → {cu.R26:.2f}%: {sg(cu.reg_share_change)} points'],
        ['Delta-G', f'{sg(cu.dG)}{A}'],
        ['Reverse step: Delta-G - affiliation-share loss', f'{cu.dG:.2f} - {cu.reg_share_loss:.2f} = **{sg(cu.residual)}{A}** (the residual)'],
        ['Implied extra votes = D 2026 - S 2022 x ballots 2026', f'{i(cu.D26)}{A} - {cu.S22:.2f}% x {i(cu.ballots26)}{A} = **{sg(cu.residual_votes, 0)}{A}**'],
        ['Registration-scaled gap (Nebraska "gap in votes" line)', f'{i(cu.D26)}{A} - {i(cu.D22)} x ({i(cu.demreg26)} / {i(cu.demreg22)}) = {sg(cu.gap_votes_ne_style, 0)}{A}']]), '',
      f'Statewide offset need for the {T["reg_share_loss"]:.2f}-point affiliation-share decline: switched votes = s x N, added votes = s x N / (1 - p + s), where s is the decline (plus any cushion), N is 2026 ballots and p the 2026 Democratic share of ballots.', '',
      table(['Cushion', 'Switched votes', 'Added votes'], [['none', i(T['offset_flips_0']), i(T['offset_additions_0'])], ['1 point', i(T['offset_flips_1']), i(T['offset_additions_1'])], ['2 points', i(T['offset_flips_2']), i(T['offset_additions_2'])]]), '',
      '## Step 3: Ohio constant', '',
      'Fit from Ohio data only, each county weighted equally (ordinary least squares).', '',
      table(['Fit', 'Intercept', 'Slope', 'R²', 'n'], [
        ['Delta-G on affiliation-share drop (**Ohio constant**)', sg(k['intercept']), f'{k["slope"]:.2f} (95% CI {k["slope_lo"]:.2f} to {k["slope_hi"]:.2f})', f'{k["r2"]:.2f}', '88'],
        ['Same, narrowed', sg(kn['intercept']), f'{kn["slope"]:.2f}', f'{kn["r2"]:.2f}', str(kn['n'])],
        ['Forward fit 2022: G on R/100', sg(f22['b']), f'{f22["m"]:.1f} (SE {f22["m_se"]:.1f})', f'{f22["r2"]:.2f}', '88'],
        [f'Forward fit 2026{A}: G on R/100', sg(f26['b']), f'{f26["m"]:.1f} (SE {f26["m_se"]:.1f})', f'{f26["r2"]:.2f}', '88'],
        ['Forward fit 2022, narrowed', sg(n22['b']), f'{n22["m"]:.1f}', f'{n22["r2"]:.2f}', str(n22['n'])],
        [f'Forward fit 2026{A}, narrowed', sg(n26['b']), f'{n26["m"]:.1f}', f'{n26["r2"]:.2f}', str(n26['n'])]]), '',
      f'Narrowed fits drop the {len(NO)} counties with Cook\'s distance above 4/n (0.045) in the constant fit or either forward fit: {", ".join(NO)}. See {L("Floor-and-Ceiling", "Floor and Ceiling")}. The affiliation-share drop explains little of Delta-G (R² {k["r2"]:.2f}): the intercept, about {k["intercept"]:.1f} points, is a statewide shift that every county shares.', '',
      '## Step 4: regional constants', '',
      f'Regions are the SOS\'s own "Region Name" column, plus two tests the brief asked for: Appalachian Ohio (the 32 ARC counties) and large metro counties. "Common-slope intercept" is each group\'s Delta-G at zero drop when all groups share one slope ({anc["sos_region"]["common_slope"]:.2f} for SOS regions).', '',
      table(['Group', 'Counties', 'Mean Delta-G' + A, 'Common-slope intercept', 'Own constant slope', 'Forward fit 2022 m / b / R²', f'Forward fit 2026{A} m / b / R²'], reg_rows), '',
      f'- **SOS regions:** different intercepts p = {anc["sos_region"]["p_intercepts"]:.1e}, different slopes p = {anc["sos_region"]["p_slopes"]:.3f}. One statewide line does not fit every region.',
      f'- **Appalachia:** intercepts differ (p = {anc["appalachia"]["p_intercepts"]:.4f}), slopes do not (p = {anc["appalachia"]["p_slopes"]:.2f}). In 2022 the forward fit inside Appalachia is nearly flat (R² {F["groups"]["Appalachia (ARC, 32)"]["22"]["r2"]:.2f}) while the rest of Ohio fits well (R² {F["groups"]["Non-Appalachia (56)"]["22"]["r2"]:.2f}); Appalachian counties distort the statewide 2022 fit.',
      f'- **Metro:** intercepts differ (p = {anc["metro"]["p_intercepts"]:.4f}), slopes do not (p = {anc["metro"]["p_slopes"]:.2f}).', '',
      '## Solving backward: implied extra votes', '',
      'For each county, implied extra votes = 2026 Democratic votes - (2022 Democratic share of ballots x 2026 ballots): how many more Democratic votes the county cast than it would have at its 2022 share on 2026 turnout.', '',
      table(['Measure', 'Votes'], [
        ['Sum of the 88 county figures', i(T['residual_votes_county_sum']) + A],
        [f'Statewide, pooled: ({pc(T["S26"])} - {pc(T["S22"])}) x {i(T["ballots26"])} ballots', i(T['gain_over_2022_share']) + A],
        ['Raw rise in Democratic votes', f'{sg(T["D_gain"], 0)}{A} = {i(T["gain_over_2022_share"])} share gain + {i(T["turnout_part"])} from more ballots at the 2022 share'],
        ['Offset need, no cushion: switched / added', f'{i(T["offset_flips_0"])} / {i(T["offset_additions_0"])}'],
        ['Pooled gain as a multiple of the offset need', f'{T["ratio_low"]:.2f} to {T["ratio_high"]:.2f} times']]), '',
      '> **Hypothesis label.** Turning the residual into "implied extra votes" and calling them injected, switched or offset votes is a hypothesis the arithmetic cannot test. The same number reflects candidate choice, crossover voting, turnout changes and any other cause.', '',
      '## What the arithmetic cannot tell you', '',
      f'- **The control cycle is just as tight.** The same residual (vote-share change) on 2018 → 2022, official both years, has SD {S["residual_1822"]["sd"]:.2f} against {S["residual"]["sd"]:.2f}{A} now (Brown-Forsythe p = {S["bf_p_residual"]:.2f}); in that cycle it was negative in all 88 counties (median {sg(S["residual_1822"]["median"])}). A tight, one-direction residual is what a statewide swing looks like.',
      f'- **County size matters somewhat:** R² = {S["r2_dG_log10pop"]:.2f} for Delta-G against log population.',
      '- **2022 affiliation is reconstructed** from SOS voter history (see [Home](' + WIKI + '/Home#registration-data-source-and-caveat)).',
      f'- **Wyandot\'s 2026{A} ballots figure is below its votes cast** in every statewide race, which inflates its S 2026. See the over-ballot check.', '',
      '## All 88 counties', '', 'Largest to smallest population (Census V2025).', '', table(CT_H, cty_rows(t)), '', img('regloss', 'Vote-share change above the line, affiliation-share change below, population order'), '',
      '*Vote-share change (orange) and Democratic affiliation-share change (blue) for all 88 counties, largest to smallest population; black dots are Delta-G' + A + '.*', '', related('Reverse-Math')]
pages['Reverse-Math'] = '\n'.join(rm)

# ------------------------------------------------------------------ Locked-Ohio-Formula
tr = row(ce_c.county)
FIT_H = 'Statewide Fitted Equation (all 88 counties)'
heads = [FIT_H, 'The equation', 'How Ohio party affiliation is counted', 'Blank template', 'Rules for using this formula', 'Worked example: ' + tr.county + ' (ceiling county)']
fx = row('Franklin'); fx_pred = k['intercept'] + k['slope'] * fx.reg_share_loss
fit_sec = [f'## {FIT_H}', '',
      '```',
      f'Ohio equation:   Delta-G = {k["intercept"]:+.2f} + {k["slope"]:.2f} x (Dem affiliation-share drop 2022 -> 2026, points)',
      f'Four decimals:   Delta-G = {k["intercept"]:+.4f} + {k["slope"]:.4f} x (Dem affiliation-share drop 2022 -> 2026, points)',
      '```', '',
      table(['Item', 'Rounded', '4 decimals'], [
        ['Constant (intercept)', sg(k['intercept']), sg(k['intercept'], 4)],
        ['Constant standard error', f'{k["intercept_se"]:.2f}', f'{k["intercept_se"]:.4f}'],
        ['Multiplier (slope)', f'{k["slope"]:.2f}', f'{k["slope"]:.4f}'],
        ['Multiplier standard error', f'{k["slope_se"]:.2f}', f'{k["slope_se"]:.4f}'],
        ['Multiplier 95% confidence interval', f'{k["slope_lo"]:.2f} to {k["slope_hi"]:.2f}', f'{k["slope_lo"]:.4f} to {k["slope_hi"]:.4f}'],
        ['R²', f'{k["r2"]:.2f}', f'{k["r2"]:.4f}'],
        ['n (counties)', str(k['n']), str(k['n'])]]), '',
      f'Fitted by ordinary least squares across all 88 Ohio counties, each county weighted equally, using Ohio data only (no other state\'s numbers): 2022 to 2026{A} governor race, ballots denominator, SOS Democratic party-affiliation share. The shift is Delta-G (G 2026 - G 2022); the registration-share drop is R 2022 - R 2026, in points. The fit was computed in the data build (scipy) and recomputed independently in verification Pass 2 (DuckDB regression functions); the two agree to at least 9 decimal places.', '',
      f'**What it means:** across Ohio\'s counties, each 1-point drop in Democratic affiliation share goes with about {k["slope"]:.2f} points of extra Delta-G, starting from about {sg(k["intercept"])} points when the share does not fall. The fit explains about {100 * k["r2"]:.0f}% of the county-to-county differences in Delta-G; most of Ohio\'s shift is the constant that every county shares. (The line-11 residual below is Delta-G minus the drop, so the same fit written for the residual is residual = {sg(k["intercept"])} - {1 - k["slope"]:.2f} x drop.)', '',
      f'**Worked example: {fx.county}** (largest county by population):', '',
      table(['Step', 'Calculation', 'Result'], [
        ['1. R 2022', f'{i(fx.demreg22)} Democratic-affiliated / {i(fx.totreg22)} registered x 100', f'{fx.R22:.4f}'],
        ['2. R 2026', f'{i(fx.demreg26)} / {i(fx.totreg26)} x 100', f'{fx.R26:.4f}'],
        ['3. Affiliation-share drop', f'{fx.R22:.4f} - {fx.R26:.4f}', f'{fx.reg_share_loss:.4f} points'],
        ['4. Predicted Delta-G', f'{k["intercept"]:+.4f} + {k["slope"]:.4f} x {fx.reg_share_loss:.4f}', f'{sg(fx_pred, 4)}'],
        ['5. S 2022 and S 2026', f'{i(fx.D22)} / {i(fx.ballots22)} x 100; {i(fx.D26)}{A} / {i(fx.ballots26)}{A} x 100', f'{fx.S22:.4f}; {fx.S26:.4f}{A}'],
        ['6. Actual Delta-G', f'({fx.S26:.4f} - {fx.R26:.4f}) - ({fx.S22:.4f} - {fx.R22:.4f})', f'{sg(fx.dG, 4)}{A}'],
        ['7. Difference from the fitted line', f'{fx.dG:.4f} - {fx_pred:.4f} (actual - predicted)', f'{sg(fx.dG - fx_pred, 4)}{A}']]), '',
      f'Each step is computed from unrounded values, so redoing it with the 4-decimal figures shown can differ in the last digit. This difference from the fitted line is not the line-11 residual in the template below ({fx.county}: {sg(fx.residual)}{A}), which is Delta-G minus the affiliation-share drop. The line describes the county pattern; it does not prove anything.', '']
lf = ['# Locked Ohio Formula', '', BANNER, '', '## Contents', '', toc(heads), ''] + fit_sec + ['## The equation', '',
      '- **S** (Democratic vote share) = Democratic governor votes / total ballots cast x 100. Ballots cast is the SOS "Ballots Counted" column.',
      '- **R** (Democratic affiliation share) = Democratic-affiliated voters / registered voters (SOS canvass) x 100',
      '- **G** = S - R',
      '- **Delta-G** = G(2026) - G(2022) = (S2026 - S2022) - (R2026 - R2022)',
      '- **Reverse step (affiliation-loss subtraction):** residual = Delta-G - (R2022 - R2026) = S2026 - S2022',
      '- **Solved backward, implied extra votes:** D2026 - (S2022 / 100) x ballots2026',
      '- **Registration-scaled gap** (Nebraska "gap in votes" line): D2026 - D2022 x (DemAff2026 / DemAff2022)',
      f'- **Ohio constant (Ohio data only):** Delta-G = {sg(k["intercept"])} + {k["slope"]:.2f} x (R2022 - R2026); narrowed: {sg(kn["intercept"])} + {kn["slope"]:.2f} x drop',
      f'- **Forward-fit constants:** G = m x R/100 + b; 2022 m = {f22["m"]:.1f}, b = {sg(f22["b"])}; 2026{A} m = {f26["m"]:.1f}, b = {sg(f26["b"])}', '',
      '## How Ohio party affiliation is counted', '',
      'Ohio voters do not pick a party when they register. A voter is affiliated with the party whose primary ballot they voted in the current year or the two preceding calendar years (R.C. 3513.19); issues-only primary ballots do not count. 2026 uses the SOS voter-file PARTY_AFFILIATION field; 2022 applies the same rule to SOS voter history, calibrated for voters removed since 2022. Full detail: [Home](' + WIKI + '/Home#registration-data-source-and-caveat).', '',
      '## Blank template', '',
      table(['Line', 'Item', '2022', '2026' + A], [
        ['1', 'Democratic governor votes', '______', '______'], ['2', 'Total ballots cast (SOS "Ballots Counted")', '______', '______'],
        ['3', 'S = line 1 / line 2 x 100', '______', '______'], ['4', 'Democratic-affiliated voters', '______', '______'],
        ['5', 'Registered voters (SOS canvass)', '______', '______'], ['6', 'R = line 4 / line 5 x 100', '______', '______'],
        ['7', 'G = line 3 - line 6', '______', '______'], ['8', 'Delta-G = G 2026 - G 2022', '', '______'],
        ['9', 'Affiliation-share change = R 2026 - R 2022', '', '______'], ['10', 'Did Democratic affiliation fall? (line 4: 2026 < 2022)', '', 'Yes / No'],
        ['11', 'If yes: residual = line 8 - (line 6 2022 - line 6 2026)', '', '______'], ['12', 'Implied extra votes = line 1 (2026) - line 3 (2022) / 100 x line 2 (2026)', '', '______'],
        ['13', 'Registration-scaled gap = line 1 (2026) - line 1 (2022) x (line 4 2026 / line 4 2022)', '', '______'],
        ['14', 'Over-ballot check: Democratic + Republican votes > line 2?', 'Yes / No', 'Yes / No']]), '',
      '## Rules for using this formula', '',
      f'1. **If a county lost Democratic affiliation, run the residual step** (line 11) and solve backward (line 12). In Ohio {S["n_demreg_fell"]} of 88 counties lost Democratic-affiliated voters. The {len(S["nonloss_counties"])} **non-loss counties** ({", ".join(S["nonloss_counties"])}) get raw numbers only.',
      f'2. **The starting point is different in every state.** Ohio\'s statewide Delta-G is {sg(T["dG"])}{A} and its county median {sg(S["dG"]["median"])}{A}. Compare Ohio counties with Ohio\'s own range, not another state\'s.',
      f'3. **Always pull out the ceiling and floor counties.** Ceiling: {", ".join(top5)}. Floor (most Republican baseline): {", ".join(floor5)}. See {L("Floor-and-Ceiling", "Floor and Ceiling")}.',
      '4. **Check the denominator.** Run line 14 for every county; Wyandot fails it in 2026' + A + '.', '',
      f'## Worked example: {tr.county} (ceiling county)', '',
      table(['Line', 'Item', '2022', '2026' + A], [
        ['1', 'Democratic governor votes', i(tr.D22), i(tr.D26) + A], ['2', 'Total ballots cast', i(tr.ballots22), i(tr.ballots26) + A],
        ['3', 'S', f'{tr.S22:.2f}', f'{tr.S26:.2f}{A}'], ['4', 'Democratic-affiliated voters', i(tr.demreg22), i(tr.demreg26)],
        ['5', 'Registered voters', i(tr.totreg22), i(tr.totreg26)], ['6', 'R', f'{tr.R22:.2f}', f'{tr.R26:.2f}'],
        ['7', 'G', sg(tr.G22), sg(tr.G26) + A], ['8', 'Delta-G', '', sg(tr.dG) + A], ['9', 'Affiliation-share change', '', sg(tr.reg_share_change)],
        ['10', 'Affiliation fell?', '', 'Yes' if tr.demreg_change < 0 else 'No'], ['11', 'Residual', '', sg(tr.residual) + A],
        ['12', 'Implied extra votes', '', sg(tr.residual_votes, 0) + A], ['13', 'Registration-scaled gap', '', sg(tr.gap_votes_ne_style, 0) + A],
        ['14', 'Over-ballot?', 'No' if not tr.overballot_DR22 else 'Yes', 'No' if not tr.overballot_DR26 else 'Yes']]), '', related('Locked-Ohio-Formula')]
pages['Locked-Ohio-Formula'] = '\n'.join(lf)

# ------------------------------------------------------------------ Floor-and-Ceiling
heads = ['How to read floor and ceiling counties', 'Terminology', 'Ceiling detail', 'Floor detail', 'Lowest Delta-G', 'Texas-style over-ballot check', 'Counties to narrow out']
FC_H = ['County', 'Group', 'Population', 'R % 2022 → 2026', 'Dem affiliated 2022 → 2026', 'S % 2022 → 2026' + A, 'G 2022 → 2026' + A, 'Delta-G' + A, 'Residual' + A, 'Implied extra votes' + A]
def fc_rows(df, grp):
    return [[r.county, grp, i(r.population), f'{r.R22:.2f} → {r.R26:.2f}', f'{i(r.demreg22)} → {i(r.demreg26)} ({r.demreg_pct_change:+.1f}%)', f'{r.S22:.2f} → {r.S26:.2f}{A}',
             f'{sg(r.G22)} → {sg(r.G26)}{A}', sg(r.dG) + A, sg(r.residual) + A, sg(r.residual_votes, 0) + A] for r in df.itertuples()]
cdf = t[t.county.isin(top5)]; fdf = t[t.county.isin(floor5)]; ldf = t[t.county.isin(low5)]
ob = t[t.overballot_DR22 | t.overballot_DR26 | t.overballot_all22 | t.overballot_all26]
closest = t.assign(m=t.ballots26 - t.DR26).sort_values('m').head(4)
ndf = t[t.county.isin(NO)]
def reason(r):
    bits = []
    if r.county in top5: bits.append('ceiling county')
    if r.reg_share_loss > 4: bits.append(f'largest affiliation-share drops in the state ({r.reg_share_loss:.2f} points)')
    if r.population >= 300000: bits.append('large metro, high 2022 Democratic share')
    if r.R22 > 17: bits.append(f'high Democratic affiliation share ({r.R22:.1f}% in 2022)')
    if r.reg_share_loss < 0: bits.append('non-loss county')
    return '; '.join(bits) or 'high influence on the fitted line'
fc = ['# Floor and Ceiling', '', BANNER, '', '## Contents', '', toc(heads), '',
      '## How to read floor and ceiling counties', '',
      'Look for the pattern at both ends. **Ceiling counties** are the five with the highest Delta-G. **Floor counties** are the most Republican baseline: the five lowest 2022 Democratic affiliation shares, where there were the fewest Democrats to move. The single lowest Delta-G is reported separately.', '',
      f'- **Ceiling:** {ce_c.county} is the highest Delta-G in Ohio, {sg(ce_c.dG)}{A}.',
      f'- **Lowest Delta-G:** {fl_c.county}, {sg(fl_c.dG)}{A}. No Ohio county has a negative Delta-G, so the bottom is the smallest rise, not a decline.', '',
      '## Terminology', '',
      f'- **Ceiling counties:** top 5 Delta-G: ' + ', '.join(f'{c} {sg(row(c).dG)}{A}' for c in top5) + '.',
      f'- **Floor counties:** 5 lowest 2022 Democratic affiliation shares: ' + ', '.join(f'{c} {pc(row(c).R22)} (Delta-G {sg(row(c).dG)}{A})' for c in floor5) + '. ' + ' and '.join(c for c in floor5 if c in low5) + (' is' if len([c for c in floor5 if c in low5]) == 1 else ' are') + ' also among the 5 lowest Delta-G.',
      f'- **Non-loss counties:** Democratic-affiliated count did not fall: {", ".join(S["nonloss_counties"])}. Raw numbers only, no residual step.',
      f'- **Ballots fell, Democratic votes rose** ({len(S["ballots_fell_D_rose"])} counties): {", ".join(S["ballots_fell_D_rose"])}.',
      f'- **Counties above Delta-G 15:** {S["n_ceiling_gt15"]} of 88.', '',
      '## Ceiling detail', '', 'Largest to smallest population.', '', table(FC_H, fc_rows(cdf, 'Ceiling')), '',
      ' '.join(f'{len(g)} of the five ceiling counties ({", ".join(g.county)}) are in the SOS {rg} region.' for rg, g in cdf.groupby('sos_region')) + f' Trumbull also had one of the largest Democratic affiliation-share drops in Ohio ({row("Trumbull").reg_share_loss:.2f} points; Mahoning {row("Mahoning").reg_share_loss:.2f}).', '',
      '## Floor detail', '', 'Largest to smallest population.', '', table(FC_H, fc_rows(fdf, 'Floor')), '',
      f'All 5 floor counties rose less than the statewide median Delta-G ({sg(S["dG"]["median"])}{A}).' if all(row(c).dG < S['dG']['median'] for c in floor5) else '', '',
      '## Lowest Delta-G', '', table(FC_H, fc_rows(ldf, 'Lowest 5 Delta-G')), '',
      '## Texas-style over-ballot check', '',
      'Any county where Democratic + Republican governor votes exceed total ballots cast (SOS "Ballots Counted").', '',
      table(['Check', '2022 (official)', '2026' + A + ' (unofficial)'], [
        ['Dem + Rep governor votes > ballots cast', f'{len(S["overballot_DR22"])} counties', f'{len(S["overballot_DR26"])} county ({", ".join(S["overballot_DR26"])})'],
        ['All governor votes (incl. Libertarian, write-ins) > ballots cast', f'{len(S["overballot_all22"])} counties', f'{len(S["overballot_all26"])} county ({", ".join(S["overballot_all26"])})'],
        ['Smallest margin (ballots - all governor votes)', f'{i(S["min_rolloff22"])} votes', f'{i(S["min_rolloff26"])} votes (Wyandot)']]), '',
      f'**Wyandot 2026{A}:** ballots counted {i(wy.ballots26)}; Acton {i(wy.D26)} + Ramaswamy {i(wy.Rep26)} = {i(wy.DR26)} (**{i(wy.DR26 - wy.ballots26)} over**); with Kissick (L) {i(wy.Lib26)} and write-ins, {i(wy.gov_all26)} governor votes ({i(wy.gov_all26 - wy.ballots26)} over). In 2022 Wyandot had {i(wy.ballots22)} ballots and {i(wy.gov_all22)} governor votes. In the same unofficial file every statewide race in Wyandot (Attorney General, Auditor, Secretary of State, Treasurer, U.S. Senate, both Supreme Court seats) also exceeds {i(wy.ballots26)}, so the likeliest explanation is a ballots-counted figure that lags the vote totals. The SOS XML feed carries the same {i(wy.ballots26)}. This is a flag for the Wyandot County Board of Elections and the official canvass; it is not resolved here. Wyandot\'s S 2026 and Delta-G use the published figure and are marked accordingly.', '',
      'Closest to the line in 2026' + A + ':', '',
      table(['County', 'Ballots' + A, 'Dem + Rep' + A, 'Margin' + A], [[r.county, i(r.ballots26), i(r.DR26), sg(r.ballots26 - r.DR26, 0)] for r in closest.itertuples()]), '',
      '## Counties to narrow out', '',
      'Rule: Cook\'s distance above 4/n (0.045) in the Ohio constant fit or either forward fit. Cook\'s D shown as constant / 2022 forward / 2026 forward.', '',
      table(['County', 'SOS region', "Cook's D", 'Reason'], [[r.county, r.sos_region, f'{r.cooks_const:.3f} / {r.cooks22:.3f} / {r.cooks26:.3f}', reason(r)] for r in ndf.itertuples()]), '',
      img('cf', 'Ceiling and floor counties, population order'), '', '*Ceiling (top 5 Delta-G, orange) and floor (5 lowest 2022 Democratic affiliation share, green) counties, population order.*', '',
      img('dGpop', 'Delta-G for all 88 counties in population order'), '', '*All 88 counties, Delta-G' + A + ' in population order. Dashed line: median; dotted red line: Delta-G = 15.*', '', related('Floor-and-Ceiling')]
pages['Floor-and-Ceiling'] = '\n'.join(fc)

# ------------------------------------------------------------------ Graphs
G = [('County slope chart', 'slope', 'County slope chart, G 2022 to G 2026', f'Each line is one county, G 2022 to G 2026{A}. Orange: ceiling counties; green: floor counties; others colored by SOS region.'),
     ('Stacked bars', 'stacked', '2022 Democratic share of ballots plus 2026 change, population order', f'2022 Democratic share of ballots (blue) plus the 2022 to 2026{A} gain (orange), largest to smallest population.'),
     ('Affiliation loss below the line', 'regloss', 'Vote-share change above the line, affiliation-share change below', f'Vote-share change (orange) above the line, Democratic affiliation-share change (blue) below; black dots: Delta-G{A}.'),
     ('Delta-G by population order', 'dGpop', 'Delta-G for all 88 counties in population order', f'All 88 counties, largest to smallest population. Lowest: {fl_c.county}; highest: {ce_c.county}.'),
     ('Ohio constant', 'const', 'Delta-G against the affiliation-share drop with the Ohio constant line', f'Delta-G{A} against the Democratic affiliation-share drop, colored by SOS region, marker size by population. Line: Delta-G = {sg(k["intercept"])} + {k["slope"]:.2f} x drop (R² {k["r2"]:.2f}, n = 88).'),
     ('Forward fits', 'fwd', 'Forward fit of G on R, 2022 and 2026', f'G against R for 2022 and 2026{A}, with the Ohio forward-fit lines.'),
     ('Ceiling and floor counties', 'cf', 'Ceiling and floor counties, population order', 'Ceiling (top 5 Delta-G, orange) and floor (5 lowest 2022 Democratic affiliation share, green) counties.'),
     ('Texas-style over-ballot check', 'tx', 'Democratic plus Republican votes as a percent of ballots cast', f'(D + R) / ballots cast for every county, 2022 and 2026{A}. Only Wyandot 2026{A} crosses 100%.'),
     ('Control cycle', 'strip', 'Residual spread 2022 to 2026 versus 2018 to 2022', 'Residual (vote-share change) for all 88 counties, 2022 to 2026' + A + ' against the 2018 to 2022 control cycle (official both years).')]
heads = [f'{n}. {g[0]}' for n, g in enumerate(G, 1)]
gr = ['# Graphs', '', BANNER, '', 'All charts use the ballots denominator and list counties largest to smallest population unless the title says otherwise. Image files are in the [repository](' + REPO + ').', '',
      '## Contents', '', toc(heads), '']
for hd, (name, key, alt, cap) in zip(heads, G):
    gr += [f'## {hd}', '', img(key, alt), '', f'*{cap}*', '']
gr += [related('Graphs')]
pages['Graphs'] = '\n'.join(gr)

# ------------------------------------------------------------------ Ohio County PDF Information
VR = json.load(open(os.path.join(ROOT, 'verification', 'pdf_raw_check.json')))
assert VR['cells_checked'] == VR['cells_matched'] and not VR['mismatches'], 'PDF raw check not clean: do not publish'
VS = VR['statewide']
assert (VS['d22'], VS['d26'], VS['reg26'], VS['v22'], VS['v26'], VS['b22'], VS['b26']) == (T['demreg22'], T['demreg26'], T['totreg26'], T['D22'], T['D26'], T['ballots22'], T['ballots26'])
def chg(a, b): return f'{b - a:+,} ({(b - a) / a * 100:+.1f}%)'
heads = ['Download', 'What each column means', 'Statewide totals', 'How the PDF was checked', 'Notes']
pdfp = ['# Ohio County PDF Information', '', BANNER, '',
        f'One PDF with all 88 Ohio counties on {VR["pdf_pages"]} landscape pages, modeled on the Nebraska 93-county PDF '
        f'(Nebraska_93_County_Democratic_Registration_and_Vote_Change.pdf) from the [Nebraska Election Analysis wiki]({NEWIKI}), the project that began with the '
        f'[Cedar County Audit]({CEDAR}). Counties are sorted by 2026{A} Democratic affiliation share, highest first, with a statewide total row at the bottom.', '',
        '## Contents', '', toc(heads), '', '## Download', '',
        f'**[Download the PDF: {PDFNAME}]({PDFRAW})**', '',
        f'Direct link: {PDFRAW}', '',
        f'The file is also listed in the [repository]({REPO}). It was built by `scripts/build_pdf.py`.', '',
        '## What each column means', '',
        table(['Column', 'Meaning'], [
            ['County', 'Ohio county (88 rows), then a statewide total row'],
            [f'Dem Affil Share 2026 %', f'Democratic-affiliated voters in the Nov 14, 2026 SOS voter file divided by SOS canvass registered voters for Nov 3, 2026{A}. The table is sorted by this column'],
            ['Dem Affil 2022 (est.)', 'Democratic-affiliated voters for Nov 2022, **rebuilt estimate** (see Notes). Not an SOS-published figure'],
            ['Dem Affil 2026 (Nov 14 file)', 'Voters with PARTY_AFFILIATION = D in the SOS statewide voter file updated Nov 14, 2026'],
            ['Affil Change # and %', 'Dem Affil 2026 minus Dem Affil 2022 (est.), and that change as a percent of the 2022 estimate'],
            ['Dem Gov Votes 2022', 'Votes for the Democratic governor ticket (Whaley/Stephens), SOS Nov 8, 2022 official canvass'],
            [f'Dem Gov Votes 2026{A}', f'Votes for the Democratic governor ticket (Acton/Pepper), SOS Nov 3, 2026 unofficial canvass{A}'],
            ['Vote Change # and %', 'Dem Gov Votes 2026 minus 2022, and that change as a percent of the 2022 votes'],
            ['Total Ballots 2022', 'SOS "Ballots Counted", 2022 official canvass'],
            [f'Total Ballots 2026{A}', f'SOS "Ballots Counted", 2026 unofficial canvass{A}'],
            ['Ballot Change # and %', 'Total Ballots 2026 minus 2022, and that change as a percent of the 2022 ballots'],
        ]), '',
        'Row shading in the PDF: blue rows are the counties where Democratic affiliation rose from 2022 to 2026; the orange row is Wyandot, '
        f'whose unofficial 2026 ballots counted ({i(wy.ballots26)}) is below its Democratic plus Republican governor votes ({i(wy.DR26)}).', '',
        '## Statewide totals', '',
        table(['Measure', '2022', f'2026{A}', 'Change'], [
            ['Democratic affiliation (2022 est.; 2026 voter file)', i(VS['d22']), i(VS['d26']), chg(VS['d22'], VS['d26'])],
            ['Democratic affiliation share of registered voters, 2026', '', f'{VS["d26"] / VS["reg26"] * 100:.1f}%', ''],
            ['Democratic governor votes', i(VS['v22']), i(VS['v26']) + A, chg(VS['v22'], VS['v26']) + A],
            ['Total ballots counted', i(VS['b22']), i(VS['b26']) + A, chg(VS['b22'], VS['b26']) + A],
        ]), '',
        '## How the PDF was checked', '',
        f'Every cell was recomputed from the raw SOS files only, by a separate script (`scripts/verify_pdf_raw.py`) that does not read any processed table: '
        f'the 2022 and 2026 canvass spreadsheets, the 2026 SOS XML results feed, the official May 2022 primary ballots-cast file and the four SOS statewide voter files '
        f'({VR["voterfile_records"]:,} records), rerunning the 2022 affiliation rebuild from voter history. Each value was compared with the text extracted from the PDF to the displayed decimal. '
        f'Result: **{VR["cells_checked"]:,} cells checked, {VR["cells_matched"]:,} matched, {len(VR["mismatches"])} mismatched** '
        f'(89 rows x 13 numeric columns, the row order and the figures quoted in the PDF header). The 2026 spreadsheet and XML feed agree on all '
        f'{VR["xml_vs_xlsx_2026"]["fields_compared"]} county registration, ballot and Democratic-vote fields. Report: '
        f'[verification/pdf_raw_check.txt]({REPO}/blob/main/verification/pdf_raw_check.txt).', '',
        '## Notes', '',
        f'- {A}**2026 is UNOFFICIAL.** 2026 votes, ballots and registered voters come from the SOS "November 3, 2026 General Unofficial Canvass" (downloaded Nov 19, 2026 11:53 AM CST) and will change when the SOS certifies the official canvass.',
        '- **2022 affiliation is a rebuilt estimate.** Ohio has no party registration and no 2022 voter file is still published. The 2022 figure applies the R.C. 3513.19 rule (most recent partisan primary ballot, Jan 1 2020 to Nov 8 2022) to the voter history in the Nov 14, 2026 voter file, then scales each county for voters removed since 2022 using official May 2022 Democratic primary ballots. '
        f'Cuyahoga check: {i(row("Cuyahoga").demreg22)} estimated vs 183,502 in the Cuyahoga BOE Dec 1, 2022 report. Details: [Registration data source and caveat]({WIKI}/Home#registration-data-source-and-caveat).',
        '- Votes are votes for the Democratic governor candidate, not a count of affiliated Democrats who voted.', '',
        related('Ohio-County-PDF-Information')]
pages['Ohio-County-PDF-Information'] = '\n'.join(pdfp)

side = ['**Ohio Election Analysis**', '', '1. [Home](' + WIKI + '/Home)', '2. [Reverse Math](' + WIKI + '/Reverse-Math)', '3. [Locked Ohio Formula](' + WIKI + '/Locked-Ohio-Formula)',
        '4. [Floor and Ceiling](' + WIKI + '/Floor-and-Ceiling)', '5. [Graphs](' + WIKI + '/Graphs)',
        '6. [Ohio County PDF Information](' + WIKI + '/Ohio-County-PDF-Information)', '', '**Origin**', '', f'- [Cedar County Audit (Nebraska)]({CEDAR})', f'- [Data and scripts]({REPO})']
pages['_Sidebar'] = '\n'.join(side)
for name, body in pages.items():
    open(os.path.join(W, name + '.md'), 'w').write(body.rstrip() + '\n')
json.dump({'built': BUILT}, open(os.path.join(ROOT, 'data', 'wiki_build.json'), 'w'))
print({k: len(v) for k, v in pages.items()})
