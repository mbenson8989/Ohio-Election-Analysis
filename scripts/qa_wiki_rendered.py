"""Rendered-page QA. Usage: qa_wiki_rendered.py <dir of Page.html files> [--live]. With --live, fetches github.com wiki pages itself.
Checks: tables (every row same cell count as header, no leftover '|' rows rendered as paragraphs), TOC anchors resolve to heading ids,
no literal \\n / raw markdown table or fence text, no unrendered '**', images (HTTP 200), cross-links (HTTP 200), Cedar link exact, sidebar."""
import sys, re, os, urllib.request
from html.parser import HTMLParser
PAGES = ['Home', 'Reverse-Math', 'Locked-Ohio-Formula', 'Floor-and-Ceiling', 'Graphs', 'Ohio-County-PDF-Information']
WIKI = 'https://github.com/mbenson8989/Ohio-Election-Analysis/wiki'
CEDAR = 'https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki/Cedar-Audit'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/130 Safari/537.36'}
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60); return r.status, r.read().decode('utf-8', 'replace')
def status(u, cache={}):
    if u not in cache:
        try: cache[u] = urllib.request.urlopen(urllib.request.Request(u, headers=UA, method='GET'), timeout=60).status
        except Exception as e: cache[u] = getattr(e, 'code', str(e))
    return cache[u]
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.ids = set(); s.links = []; s.imgs = []; s.tables = []; s.row = None; s.text = []; s.in_body = True; s.pre = 0; s.paras = []; s.cur_p = None; s.h = None; s.htext = []
    def handle_starttag(s, t, a):
        a = dict(a)
        if 'id' in a: s.ids.add(a['id'])
        if t == 'a' and a.get('href'): s.links.append(a['href'])
        if t == 'img': s.imgs.append(a.get('data-canonical-src') or a.get('src'))
        if t == 'table': s.tables.append([])
        if t == 'tr' and s.tables: s.row = 0
        if t in ('td', 'th') and s.row is not None: s.row += 1
        if t == 'pre': s.pre += 1
        if t == 'p': s.cur_p = []
        if re.fullmatch(r'h[1-6]', t): s.h = []
    def handle_endtag(s, t):
        if t == 'tr' and s.row is not None: s.tables[-1].append(s.row); s.row = None
        if t == 'pre': s.pre -= 1
        if re.fullmatch(r'h[1-6]', t) and s.h is not None: s.htext.append(''.join(s.h)); s.h = None
        if t == 'p' and s.cur_p is not None: s.paras.append(''.join(s.cur_p)); s.cur_p = None
    def handle_data(s, d):
        if not s.pre: s.text.append(d)
        if s.cur_p is not None: s.cur_p.append(d)
        if s.h is not None: s.h.append(d)
def body_of(html, live):
    if not live: return html
    m = re.search(r'<div class="markdown-body">(.*?)</div>\s*</div>\s*<div[^>]*(?:wiki-rightbar|gollum-editor|Layout-sidebar)', html, re.S)
    i = html.find('markdown-body'); return html[i:] if i >= 0 else html
def check(name, html, live, sidebar_html=None):
    pr = []
    p = P(); p.feed(body_of(html, live))
    for k, tb in enumerate(p.tables):
        if len(set(tb)) > 1: pr.append(f'table {k+1}: row cell counts {sorted(set(tb))}')
    for para in p.paras:
        if para.strip().startswith('|') or re.search(r'\|\s*---', para): pr.append(f'raw table text in paragraph: {para[:80]!r}')
        if '```' in para: pr.append(f'raw code fence in paragraph: {para[:80]!r}')
    txt = ''.join(p.text)
    if not live and not any(i.startswith('user-content-') for i in p.ids):   # markdown API omits heading ids: derive them with GitHub's slug rule
        p.ids |= {'user-content-' + re.sub(r'[^\w\- ]', '', h.strip().lower()).replace(' ', '-') for h in p.htext}
    if '\\n' in txt: pr.append('literal \\n in text')
    if re.search(r'\*\*\S', txt): pr.append('unrendered ** in text: ' + re.search(r'.{0,40}\*\*\S.{0,40}', txt).group(0))
    if re.search(r'&lt;[a-z/]', html[:0] + txt): pr.append('escaped raw HTML visible')
    for h in p.links:
        if h.startswith('#'):
            a = h[1:]
            if a not in p.ids and 'user-content-' + a not in p.ids: pr.append(f'TOC/anchor link {h} does not resolve')
    wl = [h for h in p.links if h.startswith(WIKI)]
    for h in sorted(set(wl)):
        pg = h[len(WIKI) + 1:].split('#')[0]
        if pg and pg not in PAGES and pg != '': pr.append(f'cross-link to unknown page {h}')
        if live and status(h) != 200: pr.append(f'cross-link {h} -> {status(h)}')
    ced = [h for h in p.links if 'Cedar' in h]
    if name in PAGES and CEDAR not in ced: pr.append(f'Cedar link missing/inexact: {ced}')
    if any(h != CEDAR for h in ced): pr.append(f'inexact Cedar link {ced}')
    for u in p.imgs:
        if u and not u.startswith('data:') and 'avatars' not in u and 'camo' not in u and status(u) != 200: pr.append(f'image {u} -> {status(u)}')
        if u and 'camo.githubusercontent' in u and status(u) != 200: pr.append(f'image(camo) {u} -> {status(u)}')
    if name == 'Graphs' and len([u for u in p.imgs if u and 'OH_' in u]) != 9: pr.append(f'Graphs has {len([u for u in p.imgs if u and "OH_" in u])} OH images, expected 9')
    if name == 'Ohio-County-PDF-Information':
        PDFRAW = 'https://github.com/mbenson8989/Ohio-Election-Analysis/raw/main/Ohio_88_County_Democratic_Registration_and_Vote_Change.pdf'
        if PDFRAW not in p.links: pr.append('raw PDF download link missing')
        elif status(PDFRAW) != 200: pr.append(f'raw PDF download link -> {status(PDFRAW)}')
        for h in sorted({h for h in p.links if h.startswith('https://github.com/mbenson8989/Ohio-Election-Analysis/blob/')}):
            if status(h) != 200: pr.append(f'repo link {h} -> {status(h)}')
    if live:
        if 'wiki-custom-sidebar' not in html and '_Sidebar' not in html: pr.append('custom _Sidebar not rendered')
        for pg in PAGES:
            if f'{WIKI}/{pg}' not in html and f'/mbenson8989/Ohio-Election-Analysis/wiki/{pg}' not in html: pr.append(f'sidebar/page list lacks {pg}')
        if 'UNOFFICIAL' not in html: pr.append('unofficial banner missing')
    return pr, len(p.tables), len(p.imgs)
if __name__ == '__main__':
    live = '--live' in sys.argv; d = [a for a in sys.argv[1:] if not a.startswith('--')]
    total = 0
    for name in PAGES + (['_Sidebar'] if not live else []):
        if live:
            st, html = get(f'{WIKI}/{name}')
            open(f'/tmp/ohlive_{name}.html', 'w').write(html)
            if st != 200: print(name, 'HTTP', st); total += 1; continue
        else: html = open(os.path.join(d[0], name + '.html')).read()
        pr, nt, ni = check(name, html, live)
        total += len(pr); print(f'{name}: tables={nt} imgs={ni} problems={len(pr)}'); [print('   -', x) for x in pr]
    print('TOTAL PROBLEMS', total); sys.exit(1 if total else 0)
