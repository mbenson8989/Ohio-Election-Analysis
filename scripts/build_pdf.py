"""Ohio 88-county PDF, modeled on Nebraska_93_County_Democratic_Registration_and_Vote_Change.pdf (landscape letter, navy header row
repeated on every page, sorted by 2026 Democratic share, statewide total row, legend + footnotes). Data: data/ohio_88_counties_by_population.csv (verified)."""
import os, json
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = '/usr/share/fonts/truetype/sand-box/google/'
for n, f in (('Carlito', 'Carlito/Carlito-Regular.ttf'), ('Carlito-Bold', 'Carlito/Carlito-Bold.ttf'), ('Carlito-Italic', 'Carlito/Carlito-Italic.ttf'), ('Caladea-Italic', 'Caladea/Caladea-Italic.ttf')):
    pdfmetrics.registerFont(TTFont(n, FD + f))
OUT = os.path.join(ROOT, 'Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf')
t = pd.read_csv(os.path.join(ROOT, 'data', 'ohio_88_counties_by_population.csv'))
t['share26'] = t.demreg26 / t.totreg26 * 100
t = t.sort_values(['share26', 'county'], ascending=[False, True]).reset_index(drop=True)
def n(v): return f'{int(v):,}'
def sn(v): return f'{int(v):+,}'
def pct(a, b): return f'{(b - a) / a * 100:+.1f}%'
def row(name, d22, d26, tot26, v22, v26, b22, b26):
    return [name, f'{d26 / tot26 * 100:.1f}%', n(d22), n(d26), sn(d26 - d22), pct(d22, d26), n(v22), n(v26), sn(v26 - v22), pct(v22, v26), n(b22), n(b26), sn(b26 - b22), pct(b22, b26)]
HDR = ['County', 'Dem Affil\nShare 2026 %', 'Dem Affil 2022\n(est.)', 'Dem Affil 2026\n(Nov 14 file)', 'Affil Change\n#', 'Affil Change\n%',
       'Dem Gov Votes\n2022', 'Dem Gov Votes\n2026*', 'Vote Change\n#', 'Vote Change %\n(on 2022 base)', 'Total Ballots\n2022', 'Total Ballots\n2026*', 'Ballot Change\n#', 'Ballot\nChange %']
rows = [row(r.county, r.demreg22, r.demreg26, r.totreg26, r.D22, r.D26, r.ballots22, r.ballots26) for r in t.itertuples()]
T = dict(d22=int(t.demreg22.sum()), d26=int(t.demreg26.sum()), tot26=int(t.totreg26.sum()), v22=int(t.D22.sum()), v26=int(t.D26.sum()), b22=int(t.ballots22.sum()), b26=int(t.ballots26.sum()))
S = json.load(open(os.path.join(ROOT, 'data', 'summary.json')))['statewide']
assert (T['d22'], T['d26'], T['tot26'], T['v22'], T['v26'], T['b22'], T['b26']) == (S['demreg22'], S['demreg26'], S['totreg26'], S['D22'], S['D26'], S['ballots22'], S['ballots26'])
tot = row('Statewide total', T['d22'], T['d26'], T['tot26'], T['v22'], T['v26'], T['b22'], T['b26'])
data = [HDR] + rows + [tot]
rose = [r.county for r in t.itertuples() if r.demreg26 > r.demreg22]
fell = [r.county for r in t.itertuples() if r.D26 < r.D22]
BLUE, ORANGE, NAVY = colors.HexColor('#dce9f5'), colors.HexColor('#fbe3d0'), colors.HexColor('#1f2d4d')
cw = [1.02 * inch, .68 * inch, .74 * inch, .74 * inch, .62 * inch, .62 * inch, .72 * inch, .72 * inch, .66 * inch, .78 * inch, .7 * inch, .7 * inch, .7 * inch, .55 * inch]
st = [('FONT', (0, 0), (-1, -1), 'Carlito', 7.6), ('FONT', (0, 0), (-1, 0), 'Carlito-Bold', 7.4), ('BACKGROUND', (0, 0), (-1, 0), NAVY),
      ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
      ('ALIGN', (1, 1), (-1, -1), 'RIGHT'), ('GRID', (0, 0), (-1, -1), .3, colors.HexColor('#9aa3b5')),
      ('FONT', (0, -1), (-1, -1), 'Carlito-Bold', 7.6), ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
      ('TOPPADDING', (0, 1), (-1, -1), 1.2), ('BOTTOMPADDING', (0, 1), (-1, -1), 1.2)]
for i, r in enumerate(rows, 1):
    if r[0] in rose: st.append(('BACKGROUND', (0, i), (-1, i), BLUE))
    if r[0] == 'Wyandot': st.append(('BACKGROUND', (0, i), (-1, i), ORANGE))
tbl = Table(data, colWidths=cw, repeatRows=1); tbl.setStyle(TableStyle(st))
wy = t[t.county == 'Wyandot'].iloc[0]
H = ParagraphStyle('h', fontName='Carlito-Bold', fontSize=13.5, leading=16)
SUB = ParagraphStyle('s', fontName='Caladea-Italic', fontSize=7.4, leading=9)
NOTE = ParagraphStyle('n', fontName='Caladea-Italic', fontSize=6.9, leading=8.4)
LEG = ParagraphStyle('l', fontName='Carlito', fontSize=7.4, leading=9)
top = t.iloc[0]; big = t.loc[t.demreg26.idxmax()]
story = [Paragraph('Ohio 88 Counties — Democratic Affiliation, Democratic Governor Votes and Total Ballots, 2022 vs 2026*', H), Spacer(1, 3),
  Paragraph(f'Sorted by 2026 Democratic share of affiliation (Democratic-affiliated voters ÷ all registered voters), highest first. {top.county} leads by share; {big.county} leads by raw Democratic affiliation.', SUB), Spacer(1, 6),
  Paragraph(f'*2026 figures are <b>UNOFFICIAL</b>: Ohio Secretary of State (SOS) "November 3, 2026 General Unofficial Canvass", downloaded 19 Nov 2026 11:53 AM CST; not yet certified. '
            '2022 votes and ballots: SOS November 8, 2022 Official Canvass. Ballots = SOS "Ballots Counted". Votes are votes for the Democratic governor candidate (Whaley 2022, Acton 2026), not a count of affiliated Democrats who voted.', NOTE), Spacer(1, 2),
  Paragraph('<b>Ohio has no party registration.</b> "Affiliation" is the party whose primary ballot the voter took most recently in the current or two preceding calendar years (R.C. 3513.19). '
            '2026: SOS statewide voter file (updated 14 Nov 2026), PARTY_AFFILIATION = D. <b>2022 affiliation is a rebuilt estimate</b>, not an SOS-published figure: reconstructed from the same voter file\'s primary history (2020 to Nov 2022) '
            'and scaled per county for voters removed since 2022 using official May 2022 Democratic primary ballots (Cuyahoga check: 182,437 estimated vs 183,502 county BOE). Share denominators: SOS canvass registered voters.', NOTE), Spacer(1, 2),
  Paragraph(f'<b>Wyandot:</b> in the unofficial 2026 file, Wyandot\'s ballots counted ({n(wy.ballots26)}) are fewer than its Democratic + Republican governor votes ({n(wy.D26 + wy.Rep26)}) and fewer than the votes in every statewide race; the ballots-counted figure is probably understated, so its ballot change is likely too low. Not resolved here.', NOTE), Spacer(1, 5)]
leg = Table([['Legend:', f'Democratic affiliation rose ({len(rose)}: {", ".join(rose)})', f'Ballots-counted anomaly (Wyandot)']], colWidths=[.6 * inch, 5.6 * inch, 2.2 * inch])
leg.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Carlito', 7.4), ('FONT', (0, 0), (0, 0), 'Carlito-Bold', 7.4), ('BACKGROUND', (1, 0), (1, 0), BLUE), ('BACKGROUND', (2, 0), (2, 0), ORANGE), ('LEFTPADDING', (0, 0), (-1, -1), 3)]))
story += [leg, Spacer(1, 5), tbl]
def foot(c, doc):
    c.saveState(); c.setFont('Caladea-Italic', 7)
    c.drawString(.5 * inch, .35 * inch, '*2026 figures UNOFFICIAL (not SOS-certified). Ohio "affiliation" = most recent party primary ballot; 2022 affiliation is a rebuilt estimate. Wyandot 2026 ballots counted likely understated.')
    c.drawRightString(10.5 * inch, .35 * inch, f'Page {doc.page} of {NP}'); c.restoreState()
for NP in (99, None):
    if NP is None: NP = doc.page
    doc = SimpleDocTemplate(OUT, pagesize=landscape(letter), leftMargin=.45 * inch, rightMargin=.45 * inch, topMargin=.4 * inch, bottomMargin=.55 * inch,
                            title='Ohio 88 County Democratic Registration (Affiliation) and Vote Change, 2022 vs 2026 (2026 unofficial)', author='Ohio Election Analysis (mbenson8989)')
    doc.build(list(story), onFirstPage=foot, onLaterPages=foot)
json.dump({'rows': data, 'pages': NP}, open(os.path.join(ROOT, 'data', 'pdf_expected_cells.json'), 'w'))
print(OUT, 'pages', NP, 'rose', rose, 'fell', fell)
