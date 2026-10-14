#!/usr/bin/env python3
"""Validates that router chips on Page 1 of the compiled PDF have visible borders and white fill.

Method:
  1. Rasterizes Page 1 at 200 DPI via pypdfium2.
  2. Extracts the 18 router link annotation rectangles.
  3. Samples pixels at each chip's boundary and interior to verify:
     - Border pixels (1px gray border #cbd5e1).
     - Interior white fill (#ffffff) distinct from the green container background.
  4. Saves a cropped 200-DPI PNG of the router for visual proof.
  5. Exits 0 if all 18 chips pass; exits 1 otherwise.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import numpy as np
    from PIL import Image
    import pypdfium2 as pdfium
    from pypdf import PdfReader
except ImportError as e:
    print(f"FAIL: Missing required dependency for router border check: {e}")
    sys.exit(1)


def check_router_borders(pdf_path: Path, output_png_path: Path | None = None) -> int:
    if not pdf_path.is_file():
        print(f"FAIL: PDF not found: {pdf_path}")
        return 1

    reader = PdfReader(str(pdf_path))
    p1 = reader.pages[0]
    page_h = float(p1.mediabox.height)
    page_w = float(p1.mediabox.width)

    scale = 200 / 72  # 200 DPI
    doc = pdfium.PdfDocument(str(pdf_path))
    img = doc[0].render(scale=scale).to_pil()
    arr = np.array(img)

    # Find router link annotations (middle of Page 1)
    router_annots = []
    for annot in p1.get("/Annots") or []:
        obj = annot.get_object()
        if str(obj.get("/Subtype")) == "/Link" and obj.get("/Dest") is not None:
            rect = [float(v) for v in obj.get("/Rect")]
            center_y = (rect[1] + rect[3]) / 2
            if 0.40 * page_h < center_y < 0.50 * page_h:
                router_annots.append((rect, str(obj.get("/Dest"))))

    if len(router_annots) != 18:
        print(f"FAIL: Expected 18 router links on page 1, found {len(router_annots)}")
        return 1

    # Sort in reading order (top-to-bottom, left-to-right)
    router_annots.sort(key=lambda a: (round(a[0][1], -1), a[0][0]))

    # Save cropped 200-dpi proof image
    if output_png_path is not None:
        crop_box = (int(20 * scale), int(455 * scale), int(575 * scale), int(485 * scale))
        cropped = img.crop(crop_box)
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(str(output_png_path))
        print(f"Saved 200-DPI cropped router proof to {output_png_path}")

    all_passed = True
    print("\n=== ROUTER CHIP BORDER RASTER VALIDATION (200 DPI) ===")
    for idx, (rect, dest) in enumerate(router_annots, 1):
        col0 = int(rect[0] * scale)
        col1 = int(rect[2] * scale)
        row0 = int((page_h - rect[3]) * scale)
        row1 = int((page_h - rect[1]) * scale)

        chip_crop = arr[row0:row1, col0:col1]

        # White fill inside chip (rgb == 255, 255, 255)
        white_count = int(np.sum((chip_crop[:, :, 0] == 255) & (chip_crop[:, :, 1] == 255) & (chip_crop[:, :, 2] == 255)))
        # Border pixels (gray #cbd5e1 roughly 190-225)
        border_count = int(np.sum(
            (chip_crop[:, :, 0] >= 190) & (chip_crop[:, :, 0] <= 225) &
            (chip_crop[:, :, 1] >= 200) & (chip_crop[:, :, 1] <= 230) &
            (chip_crop[:, :, 2] >= 215)
        ))

        status = "PASS" if (border_count >= 15 and white_count >= 100) else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  Chip {idx:2d} ({dest:8s}) | Border px: {border_count:3d} | White fill px: {white_count:4d} | {status}")

    if not all_passed:
        print("\nFAIL: One or more router chips missing rendered border or white fill.")
        return 1

    print("\nPASS: All 18 router chips confirmed with visible bordered boxes in rendered PDF (Exit 0).")
    return 0


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    pdf = base_dir / "master_ankle_dossier_GOLDEN.pdf"
    proof_png = base_dir / "router_proof_200dpi.png"
    sys.exit(check_router_borders(pdf, proof_png))
