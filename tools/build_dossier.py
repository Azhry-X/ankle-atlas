#!/usr/bin/env python3
"""Build the Ankle & Foot master dossier.

  python tools/build_dossier.py            # assemble HTML + render PDF + run all checks
  python tools/build_dossier.py --html     # assemble HTML only (no PDF)

Single source of truth:
  src/pages/pN.html      page bodies (content only)
  src/dossier.css        design system (shared with the ankle dossier look)
  atlas/data/tests.yaml  Atlas cards — every data-atlas="id" must exist there;
                         a ▸ is added automatically when the card has a video_url.

Authoring shortcuts inside page HTML (expanded at build time):
  <a class="test-link" data-atlas="thompson-test">Thompson test</a>
  <a class="info-icon" data-atlas="jospt-las-cpg-2021"></a>
  <a class="calc-badge" data-atlas="faam">Calc</a>      (Atlas calculator)
  <a class="calc-badge" href="https://...">FAAM</a>     (external calculator)
  <a class="guide-badge" href="https://...">JOSPT CPG</a>
"""
import re, sys, json, shutil, subprocess, pathlib, html as htmlmod

for _s in (sys.stdout, sys.stderr):  # Windows consoles: never crash on ▸ ≥ ° in messages
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'atlas'))
from config import ATLAS_BASE_URL  # noqa: E402
import yaml  # noqa: E402
from bs4 import BeautifulSoup, NavigableString, Comment  # noqa: E402

PAGES = [
    (1, 'red',    'Emergency Triage, Red Flags, Ottawa Rules, Vitals &amp; Body Chart', 'MRN'),
    (2, 'blue',   'Differential Diagnosis, Epidemiology &amp; Prognostic Trajectories', 'Patient'),
    (3, 'blue',   'Objective Examination, Range of Motion, HHD Strength &amp; Impairment Measures', 'Patient'),
    (4, 'blue',   'Ankle &amp; Foot Special Tests + Validated PROM Dashboard', 'Patient'),
    (5, 'purple', 'Post-Surgical Rehabilitation &amp; Stage Progression Criteria', 'Patient'),
    (6, 'orange', 'Electrophysical Agents, Injections, Orthoses &amp; Blood Flow Restriction', 'Patient'),
    (7, 'teal',   'Manual Therapy, Dry Needling Safety &amp; Informed Consent', 'Patient'),
    (8, 'green',  'Progressive Loading, Pain Traffic Light, Return to Sport &amp; 12-Week Log', 'Patient'),
    (9, 'slate',  'Longitudinal Session-by-Session Tracking Flowsheet &amp; Session 6 Checkpoint', 'Patient'),
]
FOOTER_LEFT = {9: ('Discharging Clinician', 'Sig.')}

ICON_INFO = ('<svg class="info-svg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" stroke="currentColor" '
             'stroke-width="2.2" fill="none"/><line x1="12" y1="16.5" x2="12" y2="10.5" stroke="currentColor" stroke-width="2.4"/>'
             '<circle cx="12" cy="7.3" r="1.4" fill="currentColor"/></svg>')
ICON_CALC = ('<svg class="badge-ico" viewBox="0 0 10 10" aria-hidden="true"><rect x=".6" y=".6" width="8.8" height="8.8" rx="1.4" fill="none" '
             'stroke="currentColor" stroke-width="1.1"/><rect x="2.2" y="2.1" width="5.6" height="1.7" rx=".3" fill="currentColor"/>'
             '<circle cx="2.9" cy="5.6" r=".62" fill="currentColor"/><circle cx="5" cy="5.6" r=".62" fill="currentColor"/>'
             '<circle cx="7.1" cy="5.6" r=".62" fill="currentColor"/><circle cx="2.9" cy="7.6" r=".62" fill="currentColor"/>'
             '<circle cx="5" cy="7.6" r=".62" fill="currentColor"/><circle cx="7.1" cy="7.6" r=".62" fill="currentColor"/></svg>')
ICON_DOC = ('<svg class="badge-ico" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 .7h4.2L8.3 2.8V9.3H2z" fill="none" stroke="currentColor" '
            'stroke-width="1.05" stroke-linejoin="round"/><path d="M6.1.8v2.1h2.1" fill="none" stroke="currentColor" stroke-width="1"/>'
            '<path d="M3.3 5h3.5M3.3 6.6h3.5M3.3 8.1h2.2" stroke="currentColor" stroke-width=".85"/></svg>')
ICON_STOP = ('<svg class="stop" viewBox="0 0 12 12" aria-hidden="true"><path d="M3.5 .5h5l3 3v5l-3 3h-5l-3-3v-5z" fill="#991b1b"/>'
             '<rect x="3" y="5.2" width="6" height="1.6" fill="#fff"/></svg>')


def load_atlas():
    data = yaml.safe_load((ROOT / 'atlas' / 'data' / 'tests.yaml').read_text(encoding='utf-8'))
    return {e['id']: e for e in data}


def page_shell(n, accent, title, hdr_label, body):
    tabs = '\n'.join(
        f'        <a class="ptab{" on" if i == n else ""}" href="#page-{i}">{i}</a>' for i in range(1, 10))
    left_a, left_b = FOOTER_LEFT.get(n, ('Clinician', 'Date'))
    return f'''
<!-- ===================== PAGE {n} ===================== -->
<div class="clinical-page" id="page-{n}" data-accent="{accent}">
  <header class="pg-hdr">
    <div class="brand">
      <div class="logo">ANK</div>
      <div>
        <div class="kicker">Ankle &amp; Foot &middot; Master Clinical Assessment &amp; Rehabilitation Dossier</div>
        <h1 class="pg-title">{title}</h1>
      </div>
    </div>
    <div class="hdr-right">
      <div class="fr"><span class="lb">{hdr_label}</span><span class="fl l"></span></div>
      <div class="pgno">{n:02d} / 09</div>
    </div>
  </header>
  <main class="pg-body">
{body}
  </main>
  <footer class="pg-ftr">
    <div class="ftr-top">
      <span><b>{left_a}</b> <span class="fl l"></span> <b>{left_b}</b> <span class="fl l"></span></span>
      <span>Underline = Atlas card &middot; &#9656; = video &middot; Evidence: <span class="eb eb-h">H</span> high <span class="eb eb-m">M</span> moderate <span class="eb eb-l">L</span> low <span class="eb eb-e">E</span> expert &middot; Confidential &middot; v2026.10</span>
    </div>
    <div class="pnav-wrap">
      <nav class="pnav" aria-label="Dossier pages">
        <span class="nl">GO TO</span>
{tabs}
      </nav>
    </div>
  </footer>
</div>'''


def table_widths(t):
    """Column count of every row of one table, honouring colspan and rowspan."""
    rows = [tr for tr in t.find_all('tr') if tr.find_parent('table') is t]
    pending, widths = {}, []
    for tr in rows:
        occupied = {c for c, n in pending.items() if n > 0}
        nxt = {c: n - 1 for c, n in pending.items() if n > 1}
        col = 0
        for cell in tr.find_all(['td', 'th'], recursive=False):
            while col in occupied:
                col += 1
            cs, rs = int(cell.get('colspan') or 1), int(cell.get('rowspan') or 1)
            for k in range(cs):
                if rs > 1:
                    nxt[col + k] = rs - 1
            col += cs
        widths.append(max([col] + [c + 1 for c in occupied]))
        pending = nxt
    return widths


def lint_structure(soup, label, problems):
    """Catch malformed markup that the browser would silently 'repair' into a broken layout:
    stray text inside table structure, a cell nested in a cell, rows with a different column count."""
    for el in soup.find_all(['table', 'thead', 'tbody', 'tfoot', 'tr']):
        for child in el.children:
            if isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip():
                problems.append(f'{label}: stray text inside <{el.name}>: "{child.strip()[:40]}"')
    for cell in soup.find_all(['td', 'th']):
        holder = cell.find_parent(['td', 'th', 'table'])
        if holder is not None and holder.name in ('td', 'th'):
            problems.append(f'{label}: <{cell.name}> nested inside <{holder.name}>: "{cell.get_text(" ", strip=True)[:40]}"')
    for t in soup.find_all('table'):
        w = table_widths(t)
        if len(set(w)) > 1:
            first = t.find(['th', 'td'])
            problems.append(f'{label}: table starting "{first.get_text(" ", strip=True)[:30] if first else ""}" '
                            f'has rows with different column counts {w}')


def expand(html_text, atlas, problems, label=''):
    soup = BeautifulSoup(html_text, 'html.parser')
    lint_structure(soup, label, problems)
    for a in soup.find_all('a'):
        classes = a.get('class') or []
        aid = a.get('data-atlas')
        if aid is not None:
            if aid not in atlas:
                problems.append(f'unknown atlas id: {aid}')
            a['href'] = f'{ATLAS_BASE_URL}/#{aid}'
            del a['data-atlas']
            if 'test-link' in classes and atlas.get(aid, {}).get('video_url'):
                if 'has-video' not in classes:
                    classes.append('has-video')
                    a['class'] = classes
        if 'info-icon' in classes:
            a.clear()
            a.append(BeautifulSoup(ICON_INFO, 'html.parser'))
            a['aria-label'] = 'Open Atlas info card'
        if 'calc-badge' in classes:
            a.insert(0, BeautifulSoup(ICON_CALC, 'html.parser'))
        if 'guide-badge' in classes:
            a.insert(0, BeautifulSoup(ICON_DOC, 'html.parser'))
        href = a.get('href', '')
        if href.startswith('http'):
            a['target'] = '_blank'
            a['rel'] = 'noopener'
    for s in soup.find_all('stop'):
        s.replace_with(BeautifulSoup(ICON_STOP, 'html.parser'))
    return str(soup)


def assemble():
    atlas = load_atlas()
    problems = []
    pages = []
    for n, accent, title, label in PAGES:
        p = ROOT / 'src' / 'pages' / f'p{n}.html'
        body = p.read_text(encoding='utf-8') if p.exists() else '<div class="dots fill"><span class="dots-l">Page in progress</span></div>'
        body = expand(body, atlas, problems, f'p{n}')
        pages.append(page_shell(n, accent, title, label, body))
    css = (ROOT / 'src' / 'dossier.css').read_text(encoding='utf-8')
    tmp = ROOT / 'build'
    tmp.mkdir(exist_ok=True)
    (tmp / 'content.html').write_text('\n'.join(pages), encoding='utf-8')
    (tmp / 'tw-in.css').write_text('@tailwind utilities;\n', encoding='utf-8')
    (tmp / 'tailwind.config.js').write_text(
        "module.exports={content:['%s'],corePlugins:{preflight:false},theme:{extend:{}}};\n" % (tmp / 'content.html').as_posix(),
        encoding='utf-8')
    node = shutil.which('node') or ('C:/Program Files/nodejs/node.exe' if pathlib.Path('C:/Program Files/nodejs/node.exe').exists() else None)
    cli = ROOT / 'node_modules' / 'tailwindcss' / 'lib' / 'cli.js'
    if not node or not cli.exists():
        sys.exit('Tailwind CLI not found. Install Node.js, then run "npm install" once in the project folder.')
    r = subprocess.run([str(node), str(cli), '-c', str(tmp / 'tailwind.config.js'), '-i', str(tmp / 'tw-in.css'),
                        '-o', str(tmp / 'tw-out.css'), '--minify'], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit('Tailwind build failed')
    tw = (tmp / 'tw-out.css').read_text(encoding='utf-8')
    doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ankle &amp; Foot Master Dossier</title>
<meta name="description" content="9-page A4 master clinical assessment and rehabilitation dossier for the ankle and foot: triage and red flags, differential diagnosis and prognosis, objective examination, special tests and PROMs, post-surgical and progression criteria, EPAs, injections and orthoses, manual therapy and needling, exercise and return to sport, and flowsheet. Companion Test Atlas: {ATLAS_BASE_URL}">
<style>
{css}
/* ---- compiled utility classes (Tailwind v3, generated at build) ---- */
{tw}
</style>
</head>
<body>
{"".join(pages)}
</body>
</html>
'''
    out = ROOT / 'master_ankle_dossier.html'
    out.write_text(doc, encoding='utf-8')
    return out, problems


if __name__ == '__main__':
    out, problems = assemble()
    print('HTML ->', out)
    if problems:
        print('PROBLEMS:'); [print('  -', p) for p in problems]
        sys.exit(1)
    if '--html' in sys.argv:
        sys.exit(0)
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'render_and_check.py')], cwd=ROOT)
    sys.exit(r.returncode)
