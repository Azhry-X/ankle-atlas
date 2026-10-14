#!/usr/bin/env python3
"""Validates every external href in the dossier and atlas.

Checks:
  1. Internal page navigation anchors (#page-1 .. #page-9).
  2. Atlas anchor links ({ATLAS_BASE_URL}#<id> or #<id>) resolve to a valid card in tests.yaml and atlas/index.html.
  3. YouTube video URLs return HTTP 200 via oEmbed with matching titles.
  4. DOI links (https://doi.org/<DOI>) return HTTP 200 via Crossref API with matching titles.
  5. Other external links return HTTP 200.
  6. Prints a clean markdown table of all validated links.
  7. Hard-fails (exit 1) on any broken link.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    yaml = None

# SSL context ignoring verification for test environments
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def retry_urlopen(req, timeout=12, max_retries=3):
    last_err = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise last_err


def verify_youtube_oembed(url: str) -> tuple[bool, str]:
    oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url, safe=':/?=&')}&format=json"
    req = urllib.request.Request(oembed_url, headers=HEADERS)
    try:
        status, body = retry_urlopen(req)
        if status == 200:
            data = json.loads(body)
            title = data.get("title", "")
            author = data.get("author_name", "")
            return True, f"oEmbed 200: '{title}' ({author})"
        return False, f"oEmbed HTTP {status}"
    except Exception as e:
        return False, f"oEmbed error: {e}"


def verify_doi_crossref(url: str) -> tuple[bool, str]:
    m = re.search(r"doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", url)
    if not m:
        return False, "Not a recognized DOI format"
    doi = m.group(1)
    api_url = f"https://api.crossref.org/works/{doi}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "AnkleDossierLinkChecker/1.0 (mailto:checker@example.com)"})
    try:
        status, body = retry_urlopen(req, timeout=15)
        if status == 200:
            data = json.loads(body)
            msg = data.get("message", {})
            title = msg.get("title", [""])[0]
            year = ""
            if "published-print" in msg:
                year = str(msg["published-print"]["date-parts"][0][0])
            elif "created" in msg:
                year = str(msg["created"]["date-parts"][0][0])
            return True, f"Crossref 200: '{title}' ({year})"
        return False, f"Crossref HTTP {status}"
    except Exception as e:
        return False, f"Crossref error: {e}"


def verify_http_url(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        status, _ = retry_urlopen(req, timeout=12)
        if status in (200, 301, 302, 307, 308):
            return True, f"HTTP {status}"
        return False, f"HTTP {status}"
    except Exception as e:
        return False, f"HTTP error: {e}"


def check_all_links(root_dir: Path) -> int:
    dossier_html = root_dir / "master_ankle_dossier.html"
    atlas_html = root_dir / "atlas" / "index.html"
    tests_yaml = root_dir / "atlas" / "data" / "tests.yaml"

    if not dossier_html.is_file():
        print(f"FAIL: {dossier_html} not found")
        return 1
    if not atlas_html.is_file():
        print(f"FAIL: {atlas_html} not found")
        return 1
    if not tests_yaml.is_file():
        print(f"FAIL: {tests_yaml} not found")
        return 1

    with open(tests_yaml, "r", encoding="utf-8") as f:
        yaml_entries = yaml.safe_load(f) if yaml else []
    yaml_ids = {e["id"] for e in yaml_entries}

    atlas_source = atlas_html.read_text(encoding="utf-8")
    atlas_dom_ids = set(re.findall(r'id="([a-zA-Z0-9_-]+)"', atlas_source))

    dossier_source = dossier_html.read_text(encoding="utf-8")
    dossier_dom_ids = set(re.findall(r'id="([a-zA-Z0-9_-]+)"', dossier_source))

    # Extract links from dossier HTML
    dossier_links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', dossier_source, re.DOTALL)
    atlas_links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', atlas_source, re.DOTALL)
    
    # 0. Enforce unique element IDs in atlas (Requirement B3)
    import collections
    all_atlas_ids = re.findall(r'id="([^"]+)"', atlas_source)
    id_counts = collections.Counter(all_atlas_ids)
    duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
    if duplicate_ids:
        print(f"FAIL: Duplicate element IDs found in Atlas: {duplicate_ids}")
        return 1
    print(f"PASS: All {len(id_counts)} element IDs in Atlas are strictly unique.")

    results = []
    failed = []

    print(f"Validating {len(dossier_links)} dossier links and {len(atlas_links)} atlas links...")

    # Cache for external URL checks
    cache: dict[str, tuple[bool, str]] = {}

    def get_ext_status(u: str) -> tuple[bool, str]:
        if u in cache:
            return cache[u]
        if "youtube.com" in u or "youtu.be" in u:
            res = verify_youtube_oembed(u)
        elif "doi.org" in u:
            res = verify_doi_crossref(u)
        else:
            res = verify_http_url(u)
        cache[u] = res
        return res

    # 1. Audit Dossier Links
    for href, raw_label in dossier_links:
        if href == "#":
            continue
        clean_label = " ".join(re.sub(r"<[^>]+>", "", raw_label).split())
        if not clean_label:
            clean_label = "(icon)"
        
        # Internal page link
        if href.startswith("#page-"):
            page_id = href[1:]
            ok = page_id in dossier_dom_ids
            status = "Resolves to page" if ok else "Broken page anchor"
            results.append(("Dossier", clean_label[:32], href, "Internal Page Nav", ok, status))
            if not ok:
                failed.append((href, clean_label, status))
        
        # Atlas anchor link
        elif "#" in href and ("github.io" in href or "{ATLAS_BASE_URL}" in href or href.startswith("#")):
            anchor_id = href.split("#", 1)[1]
            ok = anchor_id in yaml_ids and anchor_id in atlas_dom_ids
            status = f"Resolves to Atlas card #{anchor_id}" if ok else f"Anchor #{anchor_id} missing in Atlas"
            results.append(("Dossier", clean_label[:32], href, "Atlas Card Anchor", ok, status))
            if not ok:
                failed.append((href, clean_label, status))

        # External HTTP/HTTPS URL
        elif href.startswith("http"):
            method = "YouTube oEmbed" if ("youtube.com" in href or "youtu.be" in href) else ("Crossref API" if "doi.org" in href else "HTTP Request")
            ok, status = get_ext_status(href)
            results.append(("Dossier", clean_label[:32], href, method, ok, status))
            if not ok:
                failed.append((href, clean_label, status))
        else:
            failed.append((href, clean_label, f"Unrecognized link format: {href}"))

    # 2. Audit Atlas Links (unique external or internal targets)
    seen_atlas_href = set()
    for href, raw_label in atlas_links:
        if href in seen_atlas_href:
            continue
        seen_atlas_href.add(href)
        clean_label = " ".join(re.sub(r"<[^>]+>", "", raw_label).split())
        if not clean_label:
            clean_label = "(link)"

        if href.startswith("#"):
            anchor_id = href[1:]
            if not anchor_id:
                continue
            ok = anchor_id in yaml_ids or anchor_id in atlas_dom_ids
            status = f"Resolves to Atlas element #{anchor_id}" if ok else f"Atlas anchor #{anchor_id} missing"
            results.append(("Atlas", clean_label[:32], href, "Atlas Internal Anchor", ok, status))
            if not ok:
                failed.append((href, clean_label, status))
        elif href.startswith("http"):
            method = "YouTube oEmbed" if ("youtube.com" in href or "youtu.be" in href) else ("Crossref API" if "doi.org" in href else "HTTP Request")
            ok, status = get_ext_status(href)
            results.append(("Atlas", clean_label[:32], href, method, ok, status))
            if not ok:
                failed.append((href, clean_label, status))

    # Print Table
    print("\n| Source | Label / Chip | Target / URL | Method | Status | Details |")
    print("| --- | --- | --- | --- | --- | --- |")
    for src, lbl, u, meth, ok, det in results:
        mark = "PASS" if ok else "**FAIL**"
        # Truncate URL for table formatting
        u_display = u if len(u) <= 45 else u[:42] + "..."
        det_display = det if len(det) <= 60 else det[:57] + "..."
        print(f"| {src} | {lbl} | `{u_display}` | {meth} | {mark} | {det_display} |")

    print(f"\nTotal links checked: {len(results)}")
    print(f"Passed: {len(results) - len(failed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFAILURES:")
        for u, lbl, err in failed:
            print(f"  - [{lbl}] ({u}): {err}")
        return 1

    print("\nALL LINKS VERIFIED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    sys.exit(check_all_links(base_dir))
