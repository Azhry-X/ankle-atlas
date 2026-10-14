#!/usr/bin/env python3
"""Hard-fail checks for the ankle dossier PDF.

Fails when:
  a. any two text-bearing word rectangles intersect (interior overlap)
  b. a required red-flag label or disposition line is missing or split
  c. the rendered page count is not 9

Optional second argument is the source HTML, used to flag unbalanced tags
and duplicated restored strings. Exit 0 only when every hard check passes.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import pdfplumber
except ImportError:
    print("FAIL: pdfplumber is not installed. Install with: pip install pdfplumber pypdf")
    sys.exit(2)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


# Red-flag labels and disposition lines, in full.
REQUIRED_STRINGS = [
    "Ottawa Exclusions",
    "Wells DVT",
    "Compartment Syndrome — 6 Ps",
    "ΔP (Diastolic BP − Compartment Pressure) = ___ mmHg → ≤ 30 mmHg = EMERGENCY FASCIOTOMY INDICATED",
    "Charcot Neuroarthropathy — Neuropathic + Hot Red Foot",
    "→ IMMEDIATE total-contact offloading + urgent referral. NO loading. NO manual therapy. NO ESWT.",
    "Septic Arthritis: hot effusion · T > 38 °C · synovial WBC > 50k",
    "Acute Gout: 1st MTP erythema, exquisite pain, hx / hyperuricaemia",
    "Budapest CRPS",
    "Necrotizing fasciitis: pain out of proportion, rapid, systemic toxicity, crepitus → ED NOW",
    "Achilles Rupture Emergency Triad",
    "≥ 2 POSITIVE: Equinus boot + urgent orthopaedic referral (< 48 h). No loading.",
    "SKELETALLY IMMATURE?",
    "Salter-Harris, not sprain",
    "TRIAGE DISPOSITION:",
    "Cleared — proceed",
    "Imaging referral",
    "Urgent orthopaedic",
    "Emergency Department NOW",
    "CAUDA EQUINA RED FLAG — saddle anaesthesia · bladder / bowel dysfunction · bilateral leg signs · sexual dysfunction → EMERGENCY MRI / ED same day",
    "A · SIMPLE:",
    "B · COMPLEX:",
    "C · POST-OP:",
    "1 → 6 → 7 → 9",
    "1 → 2 → 3 → 4 → 6 → 7 → 8 → 9",
    "1 → 5 → 6 → 7 → 8 → 9",
    "♂ ≥ 32–37 · ♀ ≥ 27–31 · Ath ≥ 38–45 · LSI ≥ 90%",
    "Males 32–37 · Females 27–31 · Athletes ≥ 38–45+ reps",
    "Cleared — full RTS",
    "Modified training",
    "Not cleared",
    "Electrotherapy — TENS · IFC · NMES · HVPC · Iontophoresis",
    "Manual Release & Cupping",
    "Intensity is the dominant TENS parameter — under-dosing is the commonest failure. · Daily identical TENS produces tolerance in ~5 days: vary frequency or use mixed mode. · NMES works best superimposed on voluntary contraction, not as a replacement.",
    "CI: pacemaker / ICD · carotid sinus / anterior neck · pregnancy (abdomen, low back) · over DVT · active malignancy in field · broken skin · impaired sensation · epilepsy (head/neck) · transthoracic placement.",
    "CI: anticoagulants / bleeding disorders · fragile skin (elderly, chronic steroids) · over DVT / varicosities · open wounds · neuropathic / diabetic foot · active infection · pregnancy (abdomen). Wet cupping additionally: anaemia, immunosuppression.",
    "Skin-breaching: sterile single-use equipment, bloodborne-pathogen precautions. Confirm scope of practice & licensure before use.",
    "CONSENT OBTAINED FOR:",
    "Cupping (dry / wet)",
    "Grade III–IV manual therapy",
    "CONSENT OBTAINED FOR: ESWT Dry needling Grade III–IV manual therapy Cupping (dry / wet) | Risks & alternatives discussed | Patient may decline",
    "Objective Re-test Milestones",
]

FORBIDDEN_STRINGS = [
    "Clear -> Page 6 & Page 8",
    "Clear → Page 6 & Page 8",
    "Clear -> Page 6",
    "Clear → Page 6",
    "Page 6 & Page 8",
    "C · POST-SURGICAL",
    "PATHWAY C — POST-SURGICAL",
    "PATHWAY C — POST-OP",
]

ONCE_ONLY = [
    "ΔP (Diastolic BP − Compartment Pressure) = ___ mmHg → ≤ 30 mmHg = EMERGENCY FASCIOTOMY INDICATED",
    "Septic Arthritis: hot effusion · T > 38 °C · synovial WBC > 50k",
    "Acute Gout: 1st MTP erythema, exquisite pain, hx / hyperuricaemia",
    "A · SIMPLE:",
    "B · COMPLEX:",
    "C · POST-OP:",
    "♂ ≥ 32–37 · ♀ ≥ 27–31 · Ath ≥ 38–45 · LSI ≥ 90%",
]


def word_boxes(page):
    boxes = []
    for word in page.extract_words(use_text_flow=False, keep_blank_chars=False) or []:
        text = (word.get("text") or "").strip()
        if not text:
            continue
        boxes.append(
            {
                "text": text,
                "x0": float(word["x0"]),
                "x1": float(word["x1"]),
                "top": float(word["top"]),
                "bottom": float(word["bottom"]),
            }
        )
    return boxes


def intersections(boxes, eps=0.8):
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            ix = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
            iy = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
            if ix > eps and iy > eps:
                hits.append((a, b, ix, iy))
                if len(hits) >= 12:
                    return hits
    return hits


def line_groups(boxes):
    """Cluster words into visual lines, split wide gaps into columns, then wrap-join."""
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda w: (w["top"], w["x0"]))
    lines = []
    for word in ordered:
        if lines and abs(word["top"] - lines[-1][0]["top"]) <= 2.4:
            lines[-1].append(word)
        else:
            lines.append([word])
    groups = []
    for line in lines:
        line.sort(key=lambda w: w["x0"])
        segments = [[line[0]]]
        for word in line[1:]:
            if word["x0"] - segments[-1][-1]["x1"] > 22:
                segments.append([word])
            else:
                segments[-1].append(word)
        for segment in segments:
            groups.append({
                "text": norm(" ".join(w["text"] for w in segment)),
                "x0": min(w["x0"] for w in segment),
                "x1": max(w["x1"] for w in segment),
                "top": min(w["top"] for w in segment),
                "bottom": max(w["bottom"] for w in segment),
            })
    return groups


def column_text(groups):
    """Join a column segment with its wrapped continuation, skipping the other column."""
    blobs = []
    for i, group in enumerate(groups):
        blob = group["text"]
        for nxt in groups[i + 1 : i + 8]:
            if nxt["top"] - group["bottom"] > 16:
                break
            if nxt["top"] + 1 < group["bottom"]:
                continue
            same_column = abs(nxt["x0"] - group["x0"]) < 18 or (
                min(group["x1"], nxt["x1"]) - max(group["x0"], nxt["x0"]) > 24
            )
            if same_column:
                blob = norm(blob + " " + nxt["text"])
                break
        blobs.append(blob)
    return blobs


def phrase_status(raw_text, groups, phrase):
    folded_doc = norm(raw_text).casefold()
    folded = norm(phrase).casefold()
    if folded in folded_doc:
        return "pass", folded_doc.count(folded)
    for blob in column_text(groups):
        folded_blob = blob.casefold()
        if folded in folded_blob:
            return "pass", folded_blob.count(folded)
    # Tokens exist somewhere but not as one phrase: split. Otherwise missing.
    tokens = folded.split()
    hay = folded_doc
    if tokens and all(token in hay for token in tokens):
        return "split", 0
    return "missing", 0


def check_links(path):
    if PdfReader is None:
        return ["pypdf is not installed; link targets were not resolved"], 0, 0, False
    reader = PdfReader(str(path))
    names = set(reader.named_destinations.keys())
    internal = 0
    external = 0
    problems = []
    seen_uri = []
    for index, page in enumerate(reader.pages):
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            if str(obj.get("/Subtype")) != "/Link":
                continue
            dest = obj.get("/Dest")
            action = obj.get("/A")
            if dest is not None:
                internal += 1
                key = str(dest)
                if key in ("/TODO-VERIFY", "TODO-VERIFY"):
                    continue
                rect = [float(v) for v in obj.get("/Rect")]
                rw, rh = rect[2] - rect[0], rect[3] - rect[1]
                page_h = float(page.mediabox.height)
                center_y = (rect[1] + rect[3]) / 2
                if center_y < page_h * 0.18:
                    if rw < 32 or rh < 32:
                        problems.append(f"page {index + 1} GO TO rect {rw:.1f}x{rh:.1f} pt is under 32x32")
                # Amendment A: every internal link rect >= 9 mm (25.5 pt) in both dimensions
                if rw < 25.4 or rh < 25.4:
                    problems.append(f"page {index + 1} internal link rect {rw:.1f}x{rh:.1f} pt is under 9 mm (25.5 pt)")
                if key not in names and ("/" + key.lstrip("/")) not in names:
                    problems.append(f"page {index + 1} dest {key} does not resolve")
                else:
                    target = reader.named_destinations.get(key) or reader.named_destinations.get("/" + key.lstrip("/"))
                    if target is None or target.get("/Page") is None:
                        problems.append(f"page {index + 1} dest {key} has no page")
            elif action is not None:
                act = action.get_object()
                if str(act.get("/S")) == "/URI":
                    external += 1
                    uri = str(act.get("/URI") or "")
                    seen_uri.append(uri)
                    if not uri.startswith("http"):
                        problems.append(f"page {index + 1} empty or non-http URI {uri!r}")
                else:
                    problems.append(f"page {index + 1} unresolved action {act.get('/S')}")
            else:
                problems.append(f"page {index + 1} link has no dest or URI")
    return problems, internal, external, not problems


VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}


EXEMPT_HREF = {"#TODO-VERIFY"}


def audit_nav(html: str):
    """Every GO TO and router chip must name an existing page."""
    problems = []
    if html.count('href="#TODO-VERIFY"') > 1:
        problems.append("unexpected duplicate #TODO-VERIFY link")
    ids = set(re.findall(r'id="(page-\d+)"', html))
    found = re.findall(
        r'<a\s+class="([^"]*\b(?:ptab|rchip)\b[^"]*)"\s+href="([^"]+)"[^>]*>([^<]*)</a>',
        html,
    )
    footer = router = 0
    for cls, href, label in found:
        label = label.strip()
        kind = "router" if "rchip" in cls else "footer"
        if kind == "footer":
            footer += 1
        else:
            router += 1
        if href in EXEMPT_HREF:
            continue
        if not href.startswith("#page-"):
            problems.append(f"{kind} link {label!r} href {href} is not a page target")
            continue
        target = href[1:]
        if label != target.split("-", 1)[1]:
            problems.append(f"{kind} label {label!r} does not name {href}")
        if target not in ids:
            problems.append(f"{kind} target {href} does not exist")
    print(f"html footer links: {footer}")
    print(f"html router links: {router}")
    if footer != 81:
        problems.append(f"expected 81 footer links, found {footer}")
    if router != 18:
        problems.append(f"expected 18 router links, found {router}")
    return problems


def check_html(path: Path):
    import html as html_lib
    raw_bytes = path.read_bytes()
    text = html_lib.unescape(raw_bytes.decode("utf-8-sig"))
    problems = []
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        problems.append("UTF-8 BOM present")
    # Comments and scripts are not walked as tags beyond a simple stack of real tags.
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", "", stripped, flags=re.S | re.I)
    tokens = re.findall(r"</?([a-zA-Z][\w:-]*)\b[^>]*?/?>", stripped)
    raw_tags = re.findall(r"<(/?)([a-zA-Z][\w:-]*)\b([^>]*)>", stripped)
    stack = []
    for slash, name, rest in raw_tags:
        name = name.lower()
        closing = bool(slash)
        self_close = rest.rstrip().endswith("/") or name in VOID
        if closing:
            if not stack or stack[-1] != name:
                problems.append(f"unbalanced closing </{name}>")
                if len(problems) > 8:
                    break
            else:
                stack.pop()
        elif not self_close:
            stack.append(name)
    if stack and len(problems) < 8:
        problems.append("unclosed tags: " + ", ".join(stack[-6:]))
    problems.extend(audit_nav(path.read_text(encoding="utf-8")))
    expected_markers = {"H": 15, "M": 7, "M*": 3, "L": 10, "L*": 4, "E": 1}
    found_markers = {}
    for token in re.findall(r"\[(M\*|L\*|H|E|M|L)\]", text):
        found_markers[token] = found_markers.get(token, 0) + 1
    if found_markers != expected_markers:
        problems.append(f"evidence-marker multiset {found_markers} != phase-2 expected {expected_markers}")
    folded = norm(text).casefold()
    for phrase in ONCE_ONLY:
        count = folded.count(norm(phrase).casefold())
        if count != 1:
            problems.append(f"HTML string count {count} for {phrase}")
    return problems


def bundled_font_names(html_path: Path):
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return set(), [], ["fontTools is not installed. Install with: pip install fonttools"]
    fonts_dir = html_path.parent / "fonts"
    names = set()
    cmaps = []
    if not fonts_dir.is_dir():
        return names, cmaps, [f"bundled fonts directory not found: {fonts_dir}"]
    files = sorted(fonts_dir.glob("*.ttf"))
    if not files:
        return names, cmaps, [f"no .ttf files in {fonts_dir}"]
    for fp in files:
        font = TTFont(fp)
        ps = font["name"].getDebugName(6)
        if ps:
            names.add(ps)
        cmap = set()
        for table in font["cmap"].tables:
            cmap.update(table.cmap.keys())
        cmaps.append(cmap)
    return names, cmaps, []


def type3_codepoints(obj):
    tu = obj.get("/ToUnicode")
    if tu is None:
        return set()
    data = tu.get_object().get_data().decode("latin1", errors="replace")
    points = set()
    for match in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", data):
        dst = match.group(2)
        if len(dst) % 4 != 0:
            continue
        raw = bytes.fromhex(dst)
        try:
            text = raw.decode("utf-16-be")
        except UnicodeDecodeError:
            continue
        for ch in text:
            points.add(ord(ch))
    return points


def check_embedded_fonts(pdf_path: Path, html_path: Path | None):
    problems = []
    seen = []
    if html_path is None or PdfReader is None:
        return ["embedded-font check needs the HTML path and pypdf"], seen
    names, cmaps, setup = bundled_font_names(html_path)
    problems.extend(setup)
    reader = PdfReader(str(pdf_path))
    for index, page in enumerate(reader.pages):
        resources = page.get("/Resources")
        if resources is None:
            continue
        fonts = resources.get_object().get("/Font")
        if not fonts:
            continue
        for ref in fonts.get_object().values():
            obj = ref.get_object()
            base = obj.get("/BaseFont")
            subtype = str(obj.get("/Subtype"))
            if base:
                raw = str(base).lstrip("/")
                if "+" in raw:
                    raw = raw.split("+", 1)[1]
                seen.append(raw)
                if raw not in names:
                    problems.append(f"page {index + 1} embedded font {raw} is not one of the bundled files")
            elif subtype == "/Type3":
                points = type3_codepoints(obj)
                outside = [cp for cp in points if not any(cp in cmap for cmap in cmaps)]
                seen.append("Type3")
                if not points:
                    problems.append(f"page {index + 1} Type3 font has no Unicode map tying it to a bundled file")
                elif outside:
                    sample = ", ".join(f"U+{cp:04X}" for cp in sorted(outside)[:6])
                    problems.append(f"page {index + 1} Type3 font uses glyphs outside the bundled fonts ({sample})")
            else:
                problems.append(f"page {index + 1} font subtype {subtype} is not a bundled file")
    return problems, sorted(set(seen))


def main():
    if len(sys.argv) < 2:
        print("usage: check_dossier.py PDF [HTML]")
        sys.exit(2)
    pdf_path = Path(sys.argv[1])
    html_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not pdf_path.is_file():
        print(f"FAIL: PDF not found: {pdf_path}")
        sys.exit(2)

    pdf = pdfplumber.open(str(pdf_path))
    page_count = len(pdf.pages)
    print(f"pages: {page_count}")
    failures = []
    if page_count != 9:
        failures.append(f"page count {page_count} != 9")
    for index, page in enumerate(pdf.pages):
        width, height = float(page.width), float(page.height)
        if abs(width - 595) > 3 or abs(height - 842) > 3:
            failures.append(f"page {index + 1} size {width:.1f}x{height:.1f} is not portrait A4")

    raw_pages = []
    all_groups = []
    collision_examples = []
    for index, page in enumerate(pdf.pages):
        boxes = word_boxes(page)
        hits = intersections(boxes)
        if hits:
            failures.append(f"page {index + 1} has {len(hits)} intersecting text boxes")
            for a, b, ix, iy in hits[:4]:
                collision_examples.append(
                    f"  p{index + 1} {a['text']!r} ∩ {b['text']!r} overlap {ix:.1f}x{iy:.1f}pt"
                )
        raw_pages.append(page.extract_text() or "")
        all_groups.extend(line_groups(boxes))
    raw = "\n".join(raw_pages)
    if collision_examples:
        print("COLLISIONS:")
        print("\n".join(collision_examples))
    else:
        print("collisions: none")

    folded = norm(raw).casefold()
    print("REQUIRED_STRINGS:")
    for phrase in REQUIRED_STRINGS:
        status, count = phrase_status(raw, all_groups, phrase)
        mark = "PASS" if status == "pass" else "FAIL"
        print(f"  {mark} {status}: {phrase}")
        if status != "pass":
            failures.append(f"required string {status}: {phrase}")
        elif count > 1 and phrase in ONCE_ONLY:
            failures.append(f"duplicated string x{count}: {phrase}")
            print(f"  FAIL duplicate x{count}")

    print("FORBIDDEN:")
    for phrase in FORBIDDEN_STRINGS:
        present = norm(phrase).casefold() in folded
        print(f"  {'FAIL present' if present else 'PASS absent'}: {phrase}")
        if present:
            failures.append(f"forbidden string present: {phrase}")

    font_problems, embedded_fonts = check_embedded_fonts(pdf_path, html_path)
    print("embedded fonts: " + (", ".join(embedded_fonts) if embedded_fonts else "none"))
    for problem in font_problems:
        print("  " + problem)
        failures.append(problem)

    link_problems, internal, external, links_ok = check_links(pdf_path)
    print(f"internal links: {internal}")
    print(f"external links: {external}")
    print(f"link targets resolve: {'yes' if links_ok else 'no'}")
    for problem in link_problems[:12]:
        print("  " + problem)
        failures.append(problem)

    if html_path is not None:
        if not html_path.is_file():
            failures.append(f"HTML not found: {html_path}")
        else:
            html_problems = check_html(html_path)
            print("html: " + ("ok" if not html_problems else "FAIL"))
            for problem in html_problems:
                print("  " + problem)
                failures.append(problem)

    if failures:
        print(f"FAIL {len(failures)} check(s)")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
