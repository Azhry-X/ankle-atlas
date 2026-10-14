# Ankle & Foot Complex — Master Clinical Dossier & Companion Test Atlas

[![Atlas Live Web App](https://img.shields.io/badge/Live%20Atlas-GitHub%20Pages-blue?style=for-the-badge&logo=github)](https://Azhry-X.github.io/ankle-atlas)
[![Clinical Entries](https://img.shields.io/badge/Clinical%20Entries-79%20Total-emerald?style=for-the-badge)](https://Azhry-X.github.io/ankle-atlas)
[![Validation](https://img.shields.io/badge/Links%20Audit-295%20Verified%20(100%25)-green?style=for-the-badge)](./tools/check_links.py)
[![PDF Dossier](https://img.shields.io/badge/Golden%20Dossier-9%20Pages%20A4-red?style=for-the-badge)](./master_ankle_dossier_GOLDEN.pdf)

> **Live Test Atlas Web App:** [https://Azhry-X.github.io/ankle-atlas](https://Azhry-X.github.io/ankle-atlas)  
> **Master Dossier PDF:** [`master_ankle_dossier_GOLDEN.pdf`](./master_ankle_dossier_GOLDEN.pdf)

---

## Overview

This repository hosts the **Ankle & Foot Complex Companion Clinical Test Atlas** and the **9-Page Master Clinical Assessment & Rehabilitation Dossier**.

The ecosystem is engineered with a strict **single-source-of-truth architecture**:
- **`atlas/data/tests.yaml`**: Definitive structured clinical database containing all 79 clinical cards (57 special tests + 22 protocol/info cards) with exact statistical diagnostic metrics ($Sn$, $Sp$, $+LR$, $-LR$, $MCID$), conservative multi-step execution procedures, positive criteria, and verified reference citations.
- **`index.html` (`/atlas/index.html`)**: Mobile-first, responsive single-page web application featuring:
  - Deep-linkable anchors (`#<id>`) for direct navigation from the dossier PDF.
  - Interactive clinical calculators: **FPI-6** (Foot Posture Index, $-12$ to $+12$), **TSK-11** (Tampa Scale of Kinesiophobia, $11$ to $44$), and **Budapest Clinical Criteria for CRPS**.
  - Verified video embeds and clinical reference DOIs.
  - Live fuzzy search across card titles, IDs, and descriptions.
- **`master_ankle_dossier.html`**: Precision-engineered 9-page A4 clinical dossier with zero text collisions, bundled fonts, interactive multi-segment routers, and subtle clinical deep links to the Atlas.

---

## Repository Structure

```
├── index.html                     # Live companion web app (GitHub Pages entry point)
├── .nojekyll                      # Prevents Jekyll processing on GitHub Pages
├── master_ankle_dossier_GOLDEN.pdf# Golden compiled 9-page A4 clinical dossier PDF
├── master_ankle_dossier.html      # Dossier source HTML (strictly 9 pages A4 portrait)
├── compile.ps1                    # Automated compilation script (Chrome Headless print)
├── validate.ps1                   # Automated validation suite
├── atlas/
│   ├── index.html                 # Atlas web app (mirror)
│   ├── config.py                  # Atlas URL and GitHub configuration
│   ├── build_atlas.py             # Build script generating index.html from tests.yaml
│   ├── data/
│   │   └── tests.yaml             # Single source of truth (79 clinical entries)
│   ├── MISSING_VIDEOS.md          # Catalog of cards pending verified clinical video
│   └── MISSING_LINKS.md           # External link audit and resolution inventory
├── fonts/                         # Embedded offline typography (Inter, Source Sans 3)
└── tools/
    ├── check_dossier.py           # Geometry, bounding box, page-count, and string verifier
    ├── check_cards.py             # Visual card overflow and boundary inspector
    └── check_links.py             # Comprehensive 295-link automated audit suite
```

---

## Live Features & Calculators

1. **Foot Posture Index (FPI-6):**
   - Direct interactive scoring ($-2$ to $+2$ across 6 criteria) producing aggregate scores from $-12$ to $+12$ with dynamic clinical interpretation.
   - Anchor: [`#fpi-6-info`](https://Azhry-X.github.io/ankle-atlas#fpi-6-info)

2. **Tampa Scale of Kinesiophobia (TSK-11):**
   - 11-item self-report questionnaire scoring 11 to 44 with clinical threshold evaluation ($>17$ high guarding).
   - Anchor: [`#tsk-11`](https://Azhry-X.github.io/ankle-atlas#tsk-11)

3. **Budapest Clinical Diagnostic Criteria for CRPS:**
   - Interactive sign/symptom matrix validating clinical diagnosis requirement ($\ge 3/4$ symptoms and $\ge 2/4$ signs).
   - Anchor: [`#budapest-crps`](https://Azhry-X.github.io/ankle-atlas#budapest-crps)

---

## Build & Validation

To rebuild the Atlas web application from `tests.yaml`:
```bash
python atlas/build_atlas.py
```

To run the complete link and dossier verification test suite:
```bash
python tools/check_links.py
python tools/check_dossier.py
```

---

## License & Attribution

Designed and maintained for clinical and academic reference in physical therapy, orthopedics, and sports medicine.
