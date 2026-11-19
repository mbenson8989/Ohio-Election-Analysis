# Ohio Election Analysis: 2022 vs 2026 Governor (Delta-G method)

> **2026 figures are UNOFFICIAL** (Ohio Secretary of State "November 3, 2026 General Unofficial Canvass", downloaded Nov 19, 2026 11:53 AM CST). 2022 figures are the SOS official canvass.

County-by-county analysis of all 88 Ohio counties using the method from Morissa Benson's [Cedar County Audit](https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki/Cedar-Audit). Write-up: **[Ohio wiki](https://github.com/mbenson8989/Ohio-Election-Analysis/wiki)** (Home, Reverse-Math, Locked-Ohio-Formula, Floor-and-Ceiling, Graphs).

## Formula

- S = Democratic governor votes / SOS "Ballots Counted" x 100
- R = Democratic-affiliated voters / SOS canvass "Registered Voters" x 100
- G = S - R; Delta-G = G(2026) - G(2022)
- Residual = Delta-G - (R2022 - R2026) = S2026 - S2022
- Implied extra votes = D2026 - S2022/100 x ballots2026 (a hypothesis label, not a finding)
- Ohio constant: OLS of Delta-G on (R2022 - R2026), Ohio counties only; forward fits G = m x R/100 + b

## Ohio has no party registration

Affiliation is the party of the voter's most recent partisan primary ballot in the current year or the two preceding calendar years (R.C. 3513.19).
- **2026:** SOS statewide voter file (SWVF, "Last Updated 14-NOV-26"), `PARTY_AFFILIATION = D`. Cross-check: SOS DATA Act election-day snapshot (Nov 3, 2026).
- **2022:** no 2022 voter file is still published. Rebuilt from SWVF voter history with the statutory rule (primaries Jan 1 2020 to Nov 8 2022, voters registered for Nov 2022), then scaled per county by official May 2022 Democratic primary ballots / surviving May 2022 Democratic primary voters in the file. Check: Cuyahoga estimate 182,437 vs Cuyahoga BOE Dec 1 2022 report 183,502. **This is an estimate, not an SOS-published number.**

## Files

| Path | What |
|---|---|
| `data/ohio_88_counties_by_population.csv` | Final table, 88 counties, sorted by population (largest first) |
| `data/summary.json` | Statewide figures, constants, regional tests, floor/ceiling, over-ballot check |
| `data/voterfile_county_aggregates_pass1.csv` | Per-county counts from the voter files |
| `verification/pass1_report.json`, `pass2_report.json` | Two independent verification passes (pass 2: separately written parsers) |
| `scripts/` | `aggregate_voterfiles.py`, `build_data.py`, `verify_pass1.py`, `verify_pass2.py`, `charts.py`, `build_wiki.py`, `qa_wiki_source.py`, `qa_wiki_rendered.py` |
| `tools/` | Browser (Chrome DevTools) download helpers used to fetch SOS files behind Cloudflare |
| `raw/` | Untouched SOS source files (see below) |
| `OH_*.png` | Charts used on the Graphs page |

Run order: `aggregate_voterfiles.py` → `build_data.py` → `verify_pass1.py` → `verify_pass2.py` → `charts.py` → `build_wiki.py`.

## Sources (raw files, unmodified)

| File in `raw/` | Source | SHA-256 |
|---|---|---|
| `2022_statewide-races-summary.xlsx` | SOS 2022 General Official Canvass, https://www.ohiosos.gov/globalassets/elections/2022/gen/statewide-races-summary.xlsx via https://web.archive.org/web/20250928223840id_/https://www.ohiosos.gov/globalassets/elections/2022/gen/statewide-races-summary.xlsx (SHA-1 equals the archive digest) | `a5ee0ac7961acaf07a184b1a854b6ab102cc5a92d13149cdb7b5867d59d95d11` |
| `2022_11-8-22-voter-turnout-summary.xlsx` | https://www.ohiosos.gov/globalassets/elections/2022/gen/11-8-22-voter-turnout-summary.xlsx via Wayback 20251204011955 (digest LS3CNYCPL64XWPU4ZFBYIDPTXEVTJ44P) | `64879c557a3d9de38f8dd601fc5b91c420eb270c8d4b4b77b8b248a06860957c` |
| `11032026GenUnTotCanSumm11192026-1753.xlsx` | https://liveresults.ohiosos.gov/Api/v1/download?filename=GeneralElectionXlsFile, Nov 19 2026 11:53 AM CST, **unofficial** | `442b96942ce7fc6b42de9087a9fda448e0edcdd970f6cb8bd41d95185fa70d88` |
| `2026_VSSC1622_NIST1500-100_20261119-1753.xml` | SOS live results NIST 1500-100 XML feed (Status UnofficialComplete), same time | `8ef7b9e193f3b37301a312b03917f3227a07c4b56b75c268f1a91cfa9db768be` |
| `crosscheck/2022-05-03_primary_ballotscastsummaryofficialresults.xlsx` | SOS May 3 2022 primary, ballots cast by party, official | `1c2672dea6f2bcfc8642ebfcad14126426ede9d97b276481fea60895228731ee` |
| `crosscheck/cuyahoga_boe_2022-12_voter_control.pdf` | Cuyahoga County BOE voter-control report, Dec 1 2022 | `f2b16246fd53604f867c4ce0bbdc82b39e27037ec7e32f2d92b371426be58819` |
| `control_2018/*` | SOS 2018 General Official Canvass (statewide by county and turnout; `_miami` = as amended by the Miami County BOE, used) | see `sha256sum` |
| `census/co-est2025-alldata.csv` | U.S. Census Bureau Vintage 2025 county population estimates | `4f5a499d851e2cb48fd7a5405e5a9235453a8a66933657aacd10df0e264f35d5` |

**Not committed (too large for GitHub), kept with checksums:**
- SOS statewide voter files `SWVF_1_22.txt.gz`, `SWVF_23_44.txt.gz`, `SWVF_45_66.txt.gz`, `SWVF_67_88.txt.gz` (560 MB, from https://www6.ohiosos.gov/ords/f?p=VOTERFTP:STWD, "Last Updated 14-NOV-26", downloaded Nov 19 2026). Checksums: `raw/voterfile_swvf_20261114_SHA256SUMS.txt`. The SOS replaces these weekly, so later downloads will differ.
- SOS DATA Act daily snapshots for Nov 3 2026, 88 county CSVs (4.3 GB, https://data.ohiosos.gov/voter). Checksums: `raw/datact_snapshot_20261103_SHA256SUMS.txt`; search response `raw/datact_snapshot_20261103/_search_20261103.json`.

## Verification

Pass 1: 3,528 figures checked, 3,528 matched, 0 mismatched. Pass 2 (independent code: raw OOXML, NIST XML, DuckDB; also refits the Ohio constant and forward fits with DuckDB regression functions): 3,454 checked, 3,454 matched, 0 mismatched. Pass 2's first run had 2 mismatches in a cross-check column caused by its own CSV escape sniffing; fixed and logged in `pass2_report.json`.
