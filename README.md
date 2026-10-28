# Ankle & Foot — Master Clinical Dossier & Companion Test Atlas

**Live Atlas:** https://azhry-x.github.io/ankle-atlas/  
**Dossier PDF:** [`master_ankle_dossier.pdf`](./master_ankle_dossier.pdf) — 9 pages, A4 portrait, built for Apple Pencil in Notability / GoodNotes.

Sister projects:
- [Knee Complex dossier + atlas](https://github.com/Azhry-X/knee-atlas) — same design system, same page architecture.
- [Lumbar Spine dossier + atlas](https://github.com/Azhry-X/lumbar-atlas) — same design system, same page architecture.
- [Shoulder Complex dossier + atlas](https://github.com/Azhry-X/shoulder-atlas) — same design system, same page architecture.
- [Cervical Spine dossier + atlas](https://github.com/Azhry-X/cervical-atlas) — same design system, same page architecture.
- [Elbow dossier + atlas](https://github.com/Azhry-X/elbow-atlas) — same design system, same page architecture.

## What is in the dossier
| Page | Content | Accent |
|---|---|---|
| 1 | Triage & red flags (Ottawa ankle & foot rules — Bachmann 2003, Dowling 2009; Achilles rupture — Maffulli 1998 → same-day referral; compartment syndrome — Ulmer 2002; DVT, septic joint, Lisfranc, neuropathic / Charcot foot, infection, ischaemic foot; vitals strip; medication & safety strip — van der Linden 2003, Wise 2012, Kearns 2019, Houghton 2010), pathway router, subjective, body chart | red |
| 2 | Differential diagnosis matrix (lateral sprain, syndesmosis sprain, CAI, midportion vs insertional Achilles tendinopathy, Achilles rupture, plantar heel pain, Morton's neuroma, tarsal tunnel, tibialis posterior dysfunction, Sever's, navicular / 5th MT stress fracture, osteochondral lesion — Luca 2025, Lisfranc, anterolateral impingement), Doherty 2014 / 2016, Sman 2015, Baltes 2022, Molloy 2003, Hutchison 2013, De Garceau 2003, Mahadevan 2015 | blue |
| 3 | Objective examination: weight-bearing lunge test (Bennell 1998), Foot Posture Index (Redmond 2008 / Rokkedal-Lausch 2013), single-leg heel-rise (Hébert-Losier 2017), JOSPT LAS CPG impairment measures (Martin 2021), ROM write-in table, HHD strength & torque / LSI write-in table | blue |
| 4 | Special tests & PROMs: lateral ligament (van Dijk 1996, JOSPT LAS CPG diagnosis quotes), syndesmosis (squeeze, external-rotation stress, fibular translation), Achilles (arc sign, Royal London, JOSPT Achilles CPG diagnosis quote), plantar fascia (windlass), forefoot / midfoot (Mulder's click, navicular drop, Lisfranc), PROM dashboard (FAAM — Martin 2005, CAIT — Hiller 2006 / Wright 2014, VISA-A — Robinson 2001, LEFS — Binkley 1999, ATRS — Nilsson-Helander 2007, CPG outcome-measure quotes) | blue |
| 5 | Post-surgical & progression criteria: surgeon-directed restrictions banner, Achilles rupture operative vs non-operative (Ochen 2019, Willits 2010, Xu 2025), lateral ligament repair (Coetzee 2018, Cho 2025), osteochondral lesion (Luca 2025), criteria to progress checklist, wound / neurovascular / boot-complaint re-check, operative log | purple |
| 6 | EPAs, injections & orthoses: shockwave & injections (Aqil 2013, Sun 2017, Rompe 2007, Whittaker 2019), JOSPT CPG quotes (LAS 2021, Achilles 2018, heel 2023), blood flow restriction (Patterson 2019, Lorenz 2021 — Cuff on the PROXIMAL THIGH only), contraindications (Houghton 2010), parameter log | orange |
| 7 | Manual therapy & needling: Weerasekara 2018, LAS CPG manual therapy, heel CPG manual therapy / stretching / taping, dry needling (Cotchett 2014, LAS CPG, heel CPG), needling safety box (Brady 2014, Boyce 2020, Halle 2016, Kearns 2019), informed consent & log | teal |
| 8 | Exercise & return to sport: loading (Alfredson 1998, Beyer 2015, Rathleff 2015, Achilles CPG), LAS CPG exercise & prevention, pain traffic light (Silbernagel 2007, Sprague 2021, Cavaggion 2024), Avoid / Modify / OK activity box, PAASS return to sport (Smith 2021) + LSI write-in, 12-week loading log | green |
| 9 | 12-visit flowsheet with patient signature column, Session 6 checkpoint box, discharge milestones & summary | slate |

Every statistic carries an evidence marker: **H** high · **M** moderate · **L** low · **E** expert opinion.
Underlined test names open the matching Atlas card; **▸** marks cards with a verified video.

## Repository layout
```
index.html                       Atlas (GitHub Pages entry point) — generated
master_ankle_dossier.html        Dossier (generated, self-contained CSS)
master_ankle_dossier.pdf         Dossier PDF (generated)
src/pages/p1.html … p9.html      Dossier page bodies  ← edit content here
src/dossier.css                  Design system
atlas/data/tests.yaml            Atlas cards: steps, criteria, accuracy, evidence, videos, calculators  ← single source of truth
atlas/build_atlas.py             Builds index.html from tests.yaml (page badges/filters = every dossier page that links the card)
atlas/config.py                  Atlas base URL
tools/build_dossier.py           Assembles HTML → PDF → runs every check
tools/render_and_check.py        Page count, overflow, overlap, fonts, required safety strings, previews
tools/check_links.py             Verifies every PDF link, Atlas anchor, card source (DOIs via the DOI registry) and video
tools/required_strings.txt       Safety-critical text that must never disappear
fonts/                           Source Sans 3 (OFL)
```

## Rebuild after an edit
One-time setup (Python 3.10+ and Node.js):
```bash
pip install -r requirements.txt
python -m playwright install chromium
npm install
```
Windows, one command (stops at the first failure):
```powershell
powershell -ExecutionPolicy Bypass -File build.ps1            # Atlas + PDF + all checks + link audit
powershell -ExecutionPolicy Bypass -File build.ps1 -SkipLinks # same, without the network link audit
```
Or step by step on any OS:
```bash
python atlas/build_atlas.py                # Atlas
python tools/build_dossier.py              # Dossier PDF + all checks (exit 1 on any problem)
python tools/check_links.py                # links (add --live after the site is published)
```

## Status
Draft cards under clinical review with open-access citations and video demonstrations.
