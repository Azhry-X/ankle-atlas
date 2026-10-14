#!/usr/bin/env python3
"""Automatically synchronize video indicators (small '▸') in the dossier from atlas/data/tests.yaml.

Rule:
  - Underline only: atlas card, no video (class="test-link")
  - Underline + small '▸': atlas card WITH a verified video (class="test-link has-video")
Can never drift because this script reads directly from tests.yaml and updates the HTML.
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

def sync_video_indicators(root_dir: Path) -> list[str]:
    dossier_html_path = root_dir / "master_ankle_dossier.html"
    tests_yaml_path = root_dir / "atlas" / "data" / "tests.yaml"

    if not dossier_html_path.is_file() or not tests_yaml_path.is_file():
        print(f"Error: Required files not found in {root_dir}")
        return []

    with open(tests_yaml_path, "r", encoding="utf-8") as f:
        yaml_entries = yaml.safe_load(f) if yaml else []

    video_card_ids = {
        e["id"] for e in yaml_entries if e.get("video_url") and str(e.get("video_url")).strip()
    }

    print(f"Loaded {len(video_card_ids)} cards with verified videos from tests.yaml:")
    for cid in sorted(video_card_ids):
        print(f"  - #{cid}")

    content = dossier_html_path.read_text(encoding="utf-8")

    # Ensure CSS rule for .test-link.has-video exists
    css_rule = """.test-link{ color:inherit; text-decoration:underline; text-decoration-color:rgba(30,58,138,0.45); text-underline-offset:2px; font-weight:inherit; transition:color 0.15s, text-decoration-color 0.15s; }
    .test-link.has-video::after{ content:" \\25B8"; font-size:0.82em; color:#1e3a8a; display:inline-block; text-decoration:none !important; font-weight:700; margin-left:1.5px; }"""
    
    if ".test-link.has-video" not in content:
        content = re.sub(
            r"\.test-link\s*\{[^}]+\}",
            lambda m: css_rule,
            content,
            count=1
        )

    # Regex to find test-link anchors
    def replacer(match):
        attrs_before = match.group(1) or ""
        curr_class = match.group(2)
        attrs_mid = match.group(3) or ""
        href = match.group(4)
        attrs_after = match.group(5) or ""
        inner = match.group(6)

        # Extract anchor ID
        anchor_match = re.search(r"#([a-zA-Z0-9_-]+)$", href)
        if not anchor_match:
            return match.group(0)
        
        cid = anchor_match.group(1)
        classes = curr_class.split()
        
        if cid in video_card_ids:
            if "has-video" not in classes:
                classes.append("has-video")
        else:
            if "has-video" in classes:
                classes.remove("has-video")
        
        new_class_str = " ".join(classes)
        return f'<a {attrs_before}class="{new_class_str}"{attrs_mid}href="{href}"{attrs_after}>{inner}</a>'

    # Pattern for <a class="...test-link..." ...href="...#cid"...>
    pattern = re.compile(
        r'<a\s+([^>]*?)class="([^"]*?\btest-link\b[^"]*?)"([^>]*?)href="([^"]+)"([^>]*?)>(.*?)</a>',
        re.DOTALL
    )

    new_content = pattern.sub(replacer, content)

    # Also handle where href appears before class
    pattern_href_first = re.compile(
        r'<a\s+([^>]*?)href="([^"]+)"([^>]*?)class="([^"]*?\btest-link\b[^"]*?)"([^>]*?)>(.*?)</a>',
        re.DOTALL
    )

    def replacer_href_first(match):
        attrs_before = match.group(1) or ""
        href = match.group(2)
        attrs_mid = match.group(3) or ""
        curr_class = match.group(4)
        attrs_after = match.group(5) or ""
        inner = match.group(6)

        anchor_match = re.search(r"#([a-zA-Z0-9_-]+)$", href)
        if not anchor_match:
            return match.group(0)
        
        cid = anchor_match.group(1)
        classes = curr_class.split()
        
        if cid in video_card_ids:
            if "has-video" not in classes:
                classes.append("has-video")
        else:
            if "has-video" in classes:
                classes.remove("has-video")
        
        new_class_str = " ".join(classes)
        return f'<a {attrs_before}href="{href}"{attrs_mid}class="{new_class_str}"{attrs_after}>{inner}</a>'

    new_content = pattern_href_first.sub(replacer_href_first, new_content)

    dossier_html_path.write_text(new_content, encoding="utf-8")

    # Also mirror to scratch directory if exists
    scratch_html = Path(r"C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\master_ankle_dossier.html")
    if scratch_html.parent.is_dir():
        scratch_html.write_text(new_content, encoding="utf-8")

    # Collect all names that got has-video
    annotated = []
    for m in re.finditer(r'<a\s+[^>]*class="[^"]*?\bhas-video\b[^"]*?"[^>]*href="[^"]*#([a-zA-Z0-9_-]+)"[^>]*>(.*?)</a>', new_content, re.DOTALL):
        cid = m.group(1)
        lbl = " ".join(re.sub(r"<[^>]+>", "", m.group(2)).split())
        annotated.append((lbl, cid))

    # Also check if href was after
    for m in re.finditer(r'<a\s+[^>]*href="[^"]*#([a-zA-Z0-9_-]+)"[^>]*class="[^"]*?\bhas-video\b[^"]*?"[^>]*>(.*?)</a>', new_content, re.DOTALL):
        cid = m.group(1)
        lbl = " ".join(re.sub(r"<[^>]+>", "", m.group(2)).split())
        annotated.append((lbl, cid))

    unique_annotated = []
    seen = set()
    for lbl, cid in annotated:
        key = (lbl, cid)
        if key not in seen:
            seen.add(key)
            unique_annotated.append((lbl, cid))

    print(f"\nSynchronized video indicators across dossier: {len(unique_annotated)} links have verified video indicator (▸):")
    for lbl, cid in unique_annotated:
        print(f"  - '{lbl}' (card #{cid})")

    return [lbl for lbl, _ in unique_annotated]

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    sync_video_indicators(base)
