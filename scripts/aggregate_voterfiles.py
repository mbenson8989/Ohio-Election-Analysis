"""PASS 1 voter-file aggregation (pandas). Reads the raw SOS voter files untouched and writes county counts.

Inputs (../raw):
  datact_snapshot_20261103/DS20261103_<COUNTY>.csv   DATA Act daily snapshot, Nov 3 2026 (election day, 4 pm)
  voterfile_swvf_20261114/SWVF_*.txt.gz              SOS weekly statewide voter file, updated 14-NOV-26

Party affiliation in Ohio is not chosen at registration. Under R.C. 3513.19 a voter is affiliated with the
party whose primary ballot they most recently voted within the current year and the two preceding calendar
years. 2026 uses the SOS PARTY_AFFILIATION column. 2022 is RECONSTRUCTED from the SOS voter-history columns
with that rule (window 2020-01-01..2022-11-08), among records that were registered for the Nov 8 2022
election (REGISTRATION_DATE <= 2022-10-11, or any vote recorded on or before 2022-11-08).
Voters removed from the rolls between 2022 and 2026 are not in any file the SOS still publishes (survivor caveat).
"""
import os, glob, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw'); OUT = os.path.join(ROOT, 'data')
REG_DEADLINE_2022 = '2022-10-11'

def ymd(col):  # 'PRIMARY-05/03/2022' -> '20220503'
    m, d, y = col.split('-', 1)[1].split('/'); return y + m + d

# ---------------- 2026 snapshot (PARTY_AFFILIATION, election day) ----------------
snap = []
for f in sorted(glob.glob(os.path.join(RAW, 'datact_snapshot_20261103', 'DS20261103_*.csv'))):
    # county-generated files differ in header case and some carry a UTF-8 BOM: normalise names only
    norm = lambda c: c.replace('\u00ef\u00bb\u00bf', '').strip().upper()
    df = pd.read_csv(f, dtype=str, usecols=lambda c: norm(c) in ('COUNTY_NUMBER', 'VOTER_STATUS', 'PARTY_AFFILIATION'),
                     keep_default_na=False, encoding='latin-1')
    df.columns = [norm(c) for c in df.columns]; assert len(df.columns) == 3, f
    df['VOTER_STATUS'] = df.VOTER_STATUS.str.upper()
    # county files code party differently (Ottawa: DEM/REP/LIB/UNA/UNK; Sandusky, Wyandot: X = unaffiliated)
    CODE = {'DEM': 'D', 'REP': 'R', 'LIB': 'L', 'GRE': 'G', 'UNA': 'U', 'UNK': 'U', 'X': 'U', '': 'U'}
    df['PARTY_AFFILIATION'] = df.PARTY_AFFILIATION.str.strip().str.upper().map(lambda v: CODE.get(v, v))
    cn = df.COUNTY_NUMBER.astype(int).unique(); assert len(cn) == 1, (f, cn)
    pa = df.PARTY_AFFILIATION.replace('', 'U').value_counts()
    snap.append(dict(county_number=int(cn[0]), file=os.path.basename(f), snap26_total=len(df),
                     snap26_active=int((df.VOTER_STATUS == 'ACTIVE').sum()),
                     snap26_D=int(pa.get('D', 0)), snap26_R=int(pa.get('R', 0)),
                     snap26_other_party=int(pa.drop(['D', 'R', 'U'], errors='ignore').sum()),
                     snap26_U=int(pa.get('U', 0))))
snap = pd.DataFrame(snap).set_index('county_number')
assert len(snap) == 88
print('snapshot done', flush=True)

# ---------------- SWVF Nov 14 2026: 2026 column + 2022 / 2026 reconstruction ----------------
rows = []
for f in sorted(glob.glob(os.path.join(RAW, 'voterfile_swvf_20261114', 'SWVF_*.txt.gz'))):
    hdr = pd.read_csv(f, nrows=0, compression='gzip').columns.tolist()
    prim = sorted([c for c in hdr if c.startswith('PRIMARY-')], key=ymd)
    hist = [c for c in hdr if c.split('-')[0] in ('PRIMARY', 'GENERAL', 'SPECIAL')]
    hist_le22 = [c for c in hist if ymd(c) <= '20221108']
    p22 = [c for c in prim if '20200101' <= ymd(c) <= '20221108']
    p26 = [c for c in prim if '20240101' <= ymd(c) <= '20261103']
    use = ['COUNTY_NUMBER', 'REGISTRATION_DATE', 'PARTY_AFFILIATION'] + hist_le22 + p26 + ['GENERAL-11/03/2026']
    use = list(dict.fromkeys(use))
    for ch in pd.read_csv(f, dtype=str, usecols=use, keep_default_na=False, compression='gzip',
                          encoding='latin-1', chunksize=500_000):
        def recon(cols):
            a = pd.Series('U', index=ch.index)
            for c in cols:                         # chronological: later primaries overwrite earlier
                v = ch[c]; m = (v != '') & (v != 'X')
                a[m] = v[m]
            return a
        a22 = recon(p22); a26 = recon(p26)
        anyvote22 = (ch[hist_le22] != '').any(axis=1)
        reg22 = (ch.REGISTRATION_DATE <= REG_DEADLINE_2022) | anyvote22
        pa = ch.PARTY_AFFILIATION.replace('', 'U')
        g = pd.DataFrame({'county_number': ch.COUNTY_NUMBER.astype(int),
            'swvf26_total': 1, 'swvf26_D': (pa == 'D').astype(int), 'swvf26_R': (pa == 'R').astype(int),
            'recon26_D': (a26 == 'D').astype(int), 'recon26_match': (a26 == pa).astype(int),
            'reg22_survivor': reg22.astype(int),
            'recon22_D': ((a22 == 'D') & reg22).astype(int), 'recon22_R': ((a22 == 'R') & reg22).astype(int),
            'surv_voted_gen22': (ch['GENERAL-11/08/2022'] != '').astype(int),
            'surv_D_prim_may22': (ch['PRIMARY-05/03/2022'] == 'D').astype(int),
            'surv_R_prim_may22': (ch['PRIMARY-05/03/2022'] == 'R').astype(int),
            'swvf_voted_gen26': (ch['GENERAL-11/03/2026'] != '').astype(int)})
        rows.append(g.groupby('county_number').sum())
    print('done', os.path.basename(f), flush=True)
sw = pd.concat(rows).groupby(level=0).sum()
assert len(sw) == 88
out = snap.join(sw, how='outer')
out.to_csv(os.path.join(OUT, 'voterfile_county_aggregates_pass1.csv'))
print(out.sum(numeric_only=True).to_string())
