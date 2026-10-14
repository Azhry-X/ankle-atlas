#!/usr/bin/env python3
"""Fail if a data-card element paints outside its data-card-box or on another page.

Uses Edge headless (Chrome if Edge is not installed) to measure layout.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROBE = r"""
<script>
window.addEventListener("load", () => setTimeout(() => {
  const fails = [];
  document.querySelectorAll("[data-card]").forEach((el) => {
    const key = el.getAttribute("data-card");
    const box = el.closest('[data-card-box="' + key + '"]');
    if (!box) {
      fails.push(key + " has no card box");
      return;
    }
    const er = el.getBoundingClientRect();
    const br = box.getBoundingClientRect();
    const ep = el.closest(".clinical-page");
    const bp = box.closest(".clinical-page");
    if (!ep || !bp || ep.id !== bp.id) {
      fails.push(key + " is not on the same page as its card");
      return;
    }
    const pad = 3;
    if (er.left < br.left - pad || er.right > br.right + pad || er.top < br.top - pad || er.bottom > br.bottom + pad) {
      fails.push(key + " renders outside its card on " + ep.id);
    }
  });
  const pre = document.createElement("pre");
  pre.id = "CARDRESULT";
  pre.textContent = fails.length ? fails.join("\n") : "PASS";
  document.body.appendChild(pre);
}, 1500));
</script>
"""

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "microsoft-edge-stable",
    "microsoft-edge",
    "google-chrome",
    "google-chrome-stable",
]


def find_browser():
    for candidate in BROWSERS:
        if Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return None


def main():
    if len(sys.argv) < 2:
        print("usage: check_cards.py HTML")
        sys.exit(2)
    html_path = Path(sys.argv[1])
    if not html_path.is_file():
        print(f"FAIL: HTML not found: {html_path}")
        sys.exit(2)
    browser = find_browser()
    if browser is None:
        print("FAIL: Microsoft Edge was not found. Install Edge, or run where google-chrome is on PATH.")
        sys.exit(2)
    source = html_path.read_text(encoding="utf-8")
    if "</body>" not in source:
        print("FAIL: HTML has no </body>")
        sys.exit(2)
    probed = source.replace("</body>", PROBE + "</body>", 1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        page = tmp_path / "cards.html"
        dom = tmp_path / "dom.html"
        err = tmp_path / "err.txt"
        page.write_text(probed, encoding="utf-8")
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--virtual-time-budget=20000",
            "--window-size=1200,1600",
            "--dump-dom",
            page.resolve().as_uri(),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=err.open("w"), timeout=40, check=False)
        dumped = proc.stdout.decode("utf-8", errors="replace")
        dom.write_text(dumped, encoding="utf-8")
    start = dumped.find('<pre id="CARDRESULT">')
    end = dumped.find("</pre>", start) if start >= 0 else -1
    if start < 0 or end < 0:
        print("FAIL: card layout probe produced no result")
        print(dumped[-400:])
        sys.exit(1)
    body = dumped[start + len('<pre id="CARDRESULT">'):end].replace("&amp;", "&")
    print(body)
    if body.strip() != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
