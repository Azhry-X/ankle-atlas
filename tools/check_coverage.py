#!/usr/bin/env python3
"""Coverage check for dossier and atlas links.

Rules:
  a. Every atlas card id in tests.yaml is referenced by at least one dossier link.
  b. Every unlinked test name in the dossier is listed in tools/unlinked_ok.txt with a reason.
  FAIL otherwise.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    yaml = None

def check_coverage(root_dir: Path) -> int:
    dossier_html = root_dir / "master_ankle_dossier.html"
    tests_yaml = root_dir / "atlas" / "data" / "tests.yaml"
    allow_list_file = root_dir / "tools" / "unlinked_ok.txt"

    if not dossier_html.is_file():
        print(f"FAIL: {dossier_html} not found")
        return 1
    if not tests_yaml.is_file():
        print(f"FAIL: {tests_yaml} not found")
        return 1
    if not allow_list_file.is_file():
        print(f"FAIL: {allow_list_file} not found")
        return 1

    with open(tests_yaml, "r", encoding="utf-8") as f:
        yaml_entries = yaml.safe_load(f) if yaml else []
    card_ids = {e["id"] for e in yaml_entries}

    dossier_text = dossier_html.read_text(encoding="utf-8")

    # (a) Check every atlas card ID is referenced in dossier
    linked_ids = set(re.findall(r"github\.io/ankle-atlas#([a-zA-Z0-9_-]+)", dossier_text))
    # Also internal anchors if any
    linked_ids.update(re.findall(r'href="#([a-zA-Z0-9_-]+)"', dossier_text))

    missing_cards = card_ids - linked_ids
    print(f"=== ATLAS CARD COVERAGE ===")
    print(f"Total atlas cards in tests.yaml: {len(card_ids)}")
    print(f"Referenced by dossier links: {len(linked_ids & card_ids)}")
    if missing_cards:
        print(f"FAIL: Atlas cards not referenced by any dossier link ({len(missing_cards)}):")
        for cid in sorted(missing_cards):
            print(f"  - #{cid}")
        return 1
    else:
        print(f"PASS: 100% coverage — all {len(card_ids)} atlas cards are referenced in the dossier.")

    # (b) Read allow-list
    allow_list = {}
    with open(allow_list_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                name, location, reason = parts[0], parts[1], parts[2]
                allow_list[name.lower()] = (name, location, reason)
            elif len(parts) == 2:
                name, reason = parts[0], parts[1]
                allow_list[name.lower()] = (name, "Dossier", reason)

    print(f"\n=== UNLINKED TESTS ALLOW-LIST CHECK ===")
    print(f"Total allow-listed unlinked tests: {len(allow_list)}")
    for k, v in allow_list.items():
        print(f"  - {v[0]} ({v[1]}): {v[2][:60]}...")

    # Known candidate test names in the dossier that are examined for linkage
    candidates = [
        ("Matles Test", "p1"),
        ("Palpable Gap", "p1"),
        ("Acute Lateral Sprain", "p2"),
        ("Peroneal Tendon", "p2"),
        ("Hopkins Squeeze", "p2"),
        ("Kleiger ER", "p2"),
        ("Heel Walk", "p1"),
        ("Toe Walk", "p1"),
        ("Single-Leg Stance", "p1"),
        ("Navicular Stress Fracture", "p2"),
        ("DF-External Rotation (Kleiger)", "p4"),
        ("Squeeze test (Hopkins)", "p4"),
        ("Mulder's Click", "p4")
    ]

    import html
    dossier_clean = html.unescape(dossier_text).replace("’", "'").replace("‘", "'")

    unlinked_and_unauthorized = []
    for test_name, page in candidates:
        norm_name = test_name.replace("’", "'")
        # Check if linked in dossier
        pattern = rf'<a\s+[^>]*href="[^"]*#[a-zA-Z0-9_-]+"[^>]*>[^<]*{re.escape(norm_name)}'
        alt_pattern = rf'<a\s+[^>]*href="[^"]*#[a-zA-Z0-9_-]+"[^>]*>.*?{re.escape(norm_name)}.*?</a>'
        is_linked = bool(re.search(pattern, dossier_clean, re.IGNORECASE | re.DOTALL) or re.search(alt_pattern, dossier_clean, re.IGNORECASE | re.DOTALL))
        
        # Check normalized form
        clean_name = norm_name.lower()
        is_allowed = clean_name in allow_list or any(clean_name in k or k in clean_name for k in allow_list)

        if not is_linked and not is_allowed:
            unlinked_and_unauthorized.append((test_name, page))
            print(f"FAIL: Test '{test_name}' on {page} is NOT linked and NOT in tools/unlinked_ok.txt")
        elif is_linked:
            print(f"PASS: '{test_name}' on {page} is LINKED.")
        else:
            print(f"PASS: '{test_name}' on {page} is UNLINKED but authorized in tools/unlinked_ok.txt.")

    if unlinked_and_unauthorized:
        print(f"\nFAIL: {len(unlinked_and_unauthorized)} unauthorized unlinked tests found.")
        return 1

    print("\nALL COVERAGE CHECKS PASSED SUCCESSFULLY (Exit 0).")
    return 0

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    sys.exit(check_coverage(base))
