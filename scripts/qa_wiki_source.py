"""Pre-push markdown lint for the wiki source: table shape, TOC anchors, code fences, stray HTML / literal \\n, link targets."""
import re, os, sys, glob
W = os.environ.get('WIKI_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'Ohio.wiki'))
PAGES = ['Home', 'Reverse-Math', 'Locked-Ohio-Formula', 'Floor-and-Ceiling', 'Graphs']
CEDAR = 'https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki/Cedar-Audit'
def slug(h): return re.sub(r'[^a-z0-9 _-]', '', h.lower()).replace(' ', '-')
def cells(l): return len(re.split(r'(?<!\\)\|', l.strip().strip('|')))
probs = []; heads = {}
for f in sorted(glob.glob(os.path.join(W, '*.md'))):
    p = os.path.basename(f)[:-3]; L = open(f).read().split('\n')
    heads[p] = {slug(re.sub(r'^#+\s*', '', l)) for l in L if l.startswith('#')}
for f in sorted(glob.glob(os.path.join(W, '*.md'))):
    p = os.path.basename(f)[:-3]; txt = open(f).read(); L = txt.split('\n')
    if txt.count('```') % 2: probs.append((p, 'unclosed code fence'))
    if re.search(r'<[a-zA-Z/][^>]*>', txt): probs.append((p, 'raw HTML tag'))
    if '\\n' in txt: probs.append((p, 'literal \\n'))
    for i, l in enumerate(L):
        if l.startswith('|'):
            prev = L[i - 1] if i else ''
            if not prev.startswith('|'):  # header row
                if i + 1 >= len(L) or not re.match(r'^\|(\s*:?-+:?\s*\|)+$', L[i + 1]): probs.append((p, f'line {i+1}: table header without separator'))
                n = cells(l); j = i + 1
                while j < len(L) and L[j].startswith('|'):
                    if cells(L[j]) != n: probs.append((p, f'line {j+1}: {cells(L[j])} cells vs header {n}'))
                    j += 1
        if l.startswith('|') and not l.rstrip().endswith('|'): probs.append((p, f'line {i+1}: row not closed with pipe'))
    for m in re.finditer(r'\]\(#([^)]+)\)', txt):
        if m.group(1) not in heads[p]: probs.append((p, f'TOC anchor #{m.group(1)} has no heading'))
    for m in re.finditer(r'\]\((https://github.com/mbenson8989/Ohio-Election-Analysis/wiki/([^)#]+)(?:#([^)]+))?)\)', txt):
        if m.group(2) not in PAGES: probs.append((p, f'link to unknown page {m.group(2)}'))
        elif m.group(3) and m.group(3) not in heads[m.group(2)]: probs.append((p, f'link anchor {m.group(2)}#{m.group(3)} missing'))
    for m in re.finditer(r'\]\((https://github.com/mbenson8989/Nebraska[^)]*)\)', txt):
        if m.group(1) not in (CEDAR, 'https://github.com/mbenson8989/Nebraska-Election-Analysis-/wiki'): probs.append((p, f'bad Nebraska link {m.group(1)}'))
    if p in PAGES and CEDAR not in txt: probs.append((p, 'no Cedar Audit link'))
    if p in PAGES and 'UNOFFICIAL' not in txt: probs.append((p, 'no unofficial banner'))
for p in PAGES + ['_Sidebar']:
    if not os.path.exists(os.path.join(W, p + '.md')): probs.append((p, 'missing'))
print('PROBLEMS:', len(probs)); [print(x) for x in probs]; sys.exit(1 if probs else 0)
