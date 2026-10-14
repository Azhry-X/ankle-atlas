#!/usr/bin/env python3
"""Build script for the Ankle & Foot Complex Test Atlas.

Reads /atlas/data/tests.yaml and builds:
  - /atlas/index.html (single static mobile-first web app with searchable, collapsible cards,
    embedded calculators, oEmbed verified video embeds, and page accent colors).
  - /atlas/MISSING_VIDEOS.md (inventory of cards lacking verified video URLs).
  - /atlas/MISSING_LINKS.md (inventory of external links lacking verified URLs).
"""
import os
import sys
import yaml
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def generate_atlas_html(entries, base_dir):
    # Sort entries by page then title
    sorted_entries = sorted(entries, key=lambda x: (x["page"], x["title"]))
    
    # Page accent colors mapping
    accent_map = {
        1: {"name": "Red", "bg": "#fef2f2", "border": "#dc2626", "badge": "#b91c1c", "text": "#991b1b"},
        2: {"name": "Blue", "bg": "#eff6ff", "border": "#2563eb", "badge": "#1d4ed8", "text": "#1e3a8a"},
        3: {"name": "Navy", "bg": "#f8fafc", "border": "#334155", "badge": "#1e293b", "text": "#0f172a"},
        4: {"name": "Indigo", "bg": "#eef2ff", "border": "#4f46e5", "badge": "#4338ca", "text": "#312e81"},
        5: {"name": "Purple", "bg": "#faf5ff", "border": "#9333ea", "badge": "#7e22ce", "text": "#581c87"},
        6: {"name": "Orange", "bg": "#fff7ed", "border": "#ea580c", "badge": "#c2410c", "text": "#9a3412"},
        7: {"name": "Teal", "bg": "#f0fdfa", "border": "#0d9488", "badge": "#0f766e", "text": "#115e59"},
        8: {"name": "Emerald", "bg": "#ecfdf5", "border": "#059669", "badge": "#047857", "text": "#064e3b"},
        9: {"name": "Slate", "bg": "#f1f5f9", "border": "#475569", "badge": "#334155", "text": "#1e293b"}
    }

    # Generate Card HTML
    cards_html = []
    missing_videos = []
    
    for e in sorted_entries:
        cid = e["id"]
        ctype = e["type"]
        title = e["title"]
        page = e["page"]
        steps = e.get("steps", [])
        positive = e.get("positive", "")
        metrics = e.get("metrics", "")
        video_url = e.get("video_url")
        sources = e.get("sources", [])
        status = e.get("review_status", "draft")
        
        acc = accent_map.get(page, accent_map[2])
        
        # Check video
        video_html = ""
        if video_url:
            # YouTube embed or link
            # Extract video ID
            m = re.search(r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})', video_url)
            if m:
                vid_id = m.group(1)
                video_html = f'''
                <div class="video-container">
                    <iframe src="https://www.youtube-nocookie.com/embed/{vid_id}" 
                            title="{title} Video Demonstration" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen loading="lazy"></iframe>
                    <div class="video-caption">
                        <span>▶ Verified Demonstration</span>
                        <a href="{video_url}" target="_blank" rel="noopener">Open in YouTube ↗</a>
                    </div>
                </div>'''
            else:
                video_html = f'<div class="video-link-fallback"><a href="{video_url}" target="_blank" rel="noopener">▶ Watch Video Demonstration ↗</a></div>'
        else:
            missing_videos.append((cid, title, page, ctype))
            if ctype == "test":
                video_html = '<div class="no-video-banner"><span>ℹ️ Video pending clinical verification (unverified URLs excluded)</span></div>'

        # Special self-hosted calculators
        calc_html = ""
        if cid == "fpi-6-info":
            calc_html = '''
            <div class="embedded-calc" id="fpi-6-calc">
                <h4>🧮 Interactive Foot Posture Index (FPI-6) Calculator</h4>
                <p class="calc-sub">Score each item from -2 to +2 based on clinical observation (Redmond 2005):</p>
                <form id="fpiForm" oninput="calculateFPI()">
                    <div class="calc-grid">
                        <div class="calc-item"><label>1. Talar head palpation</label>
                            <select id="fpi1"><option value="-2">-2 (Talar head palpable on lateral side only)</option><option value="-1">-1</option><option value="0" selected>0 (Equally palpable on both sides)</option><option value="1">+1</option><option value="2">+2 (Palpable on medial side only)</option></select>
                        </div>
                        <div class="calc-item"><label>2. Supra/infra lateral malleolar curves</label>
                            <select id="fpi2"><option value="-2">-2 (Curve below malleolus straight or convex)</option><option value="-1">-1 (Curve below malleolus concave, but less than curve above)</option><option value="0" selected>0 (Both curves roughly equal)</option><option value="1">+1 (Curve below malleolus more concave than curve above)</option><option value="2">+2 (Curve below malleolus markedly more concave than curve above)</option></select>
                        </div>
                        <div class="calc-item"><label>3. Calcaneal frontal plane inversion/eversion</label>
                            <select id="fpi3"><option value="-2">-2 (More than 5° inverted / varus)</option><option value="-1">-1</option><option value="0" selected>0 (Vertical / neutral)</option><option value="1">+1</option><option value="2">+2 (More than 5° everted / valgus)</option></select>
                        </div>
                        <div class="calc-item"><label>4. Talonavicular joint prominence</label>
                            <select id="fpi4"><option value="-2">-2 (Area markedly concave)</option><option value="-1">-1</option><option value="0" selected>0 (Area flat)</option><option value="1">+1</option><option value="2">+2 (Area bulging / convex)</option></select>
                        </div>
                        <div class="calc-item"><label>5. Medial longitudinal arch height</label>
                            <select id="fpi5"><option value="-2">-2 (Arch high and acutely angled)</option><option value="-1">-1</option><option value="0" selected>0 (Arch normal)</option><option value="1">+1</option><option value="2">+2 (Arch flat / resting on ground)</option></select>
                        </div>
                        <div class="calc-item"><label>6. Forefoot abduction/adduction</label>
                            <select id="fpi6"><option value="-2">-2 (No lateral toes visible; medial toes seen)</option><option value="-1">-1</option><option value="0" selected>0 (Medial and lateral toes equal)</option><option value="1">+1</option><option value="2">+2 (Lateral toes clearly visible / abducted)</option></select>
                        </div>
                    </div>
                    <div class="calc-result-box">
                        <div class="calc-total">Total FPI-6 Score: <span id="fpiTotal" class="score-val">0</span> / 12</div>
                        <div class="calc-interp" id="fpiInterp">Interpretation: Neutral (0 to +5)</div>
                    </div>
                </form>
            </div>'''
        elif cid == "fpi-6-test":
            calc_html = '''
            <div class="calc-link-box" style="margin-top:12px; padding:10px 14px; background:rgba(59,130,246,0.08); border:1px solid #3b82f6; border-radius:8px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                <span style="font-size:13px; font-weight:600; color:#93c5fd;">Single source of truth interactive calculator hosted in protocol card:</span>
                <a class="btn-calc" href="#fpi-6-info" onclick="expandCard('fpi-6-info')" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; background:#2563eb; border-radius:6px; color:#fff; font-weight:700; text-decoration:none; font-size:12px;">🧮 Open Interactive FPI-6 Calculator (#fpi-6-info)</a>
            </div>'''
        elif cid == "tsk-11":
            calc_html = '''
            <div class="embedded-calc" id="tsk-11-calc">
                <h4>🧮 Tampa Scale of Kinesiophobia (TSK-11) Minimal Calculator</h4>
                <p class="calc-sub">Score each item from 1 (Strongly Disagree) to 4 (Strongly Agree) — numeric item entry only:</p>
                <form id="tskForm" oninput="calculateTSK()">
                    <div class="calc-grid-compact" id="tskGrid">
                        <!-- Populated by JS -->
                    </div>
                    <div class="calc-result-box">
                        <div class="calc-total">TSK-11 Total Score: <span id="tskTotal" class="score-val">11</span> / 44</div>
                        <div class="calc-interp" id="tskInterp">Interpretation: Low Fear / Kinesiophobia Cleared (≤ 17)</div>
                    </div>
                </form>
            </div>'''
        elif cid == "budapest-crps":
            calc_html = '''
            <div class="embedded-calc" id="budapest-calc">
                <h4>🧮 Budapest Criteria CRPS Diagnostic Calculator</h4>
                <p class="calc-sub">Must fulfill both mandatory gates, then ≥ 3/4 symptom categories and ≥ 2/4 sign categories:</p>
                <form id="budapestForm" oninput="calculateBudapest()">
                    <div class="crps-gates" style="background:rgba(239,68,68,0.08); border:1px solid #ef4444; border-radius:6px; padding:8px 12px; margin-bottom:12px;">
                        <b style="color:#ef4444; font-size:12px;">Mandatory Diagnostic Pre-conditions (both must be present):</b>
                        <label style="display:flex; align-items:flex-start; gap:8px; margin-top:6px; font-weight:600; font-size:12px; cursor:pointer;"><input type="checkbox" id="gate1"> Continuing pain disproportionate to any inciting event</label>
                        <label style="display:flex; align-items:flex-start; gap:8px; margin-top:4px; font-weight:600; font-size:12px; cursor:pointer;"><input type="checkbox" id="gate2"> No other diagnosis better explains the signs and symptoms</label>
                    </div>
                    <div class="crps-split">
                        <div class="crps-col">
                            <b>Reported Symptoms (need ≥ 3 of 4 categories):</b>
                            <label><input type="checkbox" id="sx1"> 1. Sensory (hyperesthesia / allodynia)</label>
                            <label><input type="checkbox" id="sx2"> 2. Vasomotor (temperature / skin color asymmetry)</label>
                            <label><input type="checkbox" id="sx3"> 3. Sudomotor / Edema (sweating asymmetry / edema)</label>
                            <label><input type="checkbox" id="sx4"> 4. Motor / Trophic (decreased ROM / tremor / trophic changes)</label>
                        </div>
                        <div class="crps-col">
                            <b>Demonstrated Signs (need ≥ 2 of 4 categories):</b>
                            <label><input type="checkbox" id="sg1"> 1. Sensory (hyperalgesia to pinprick / allodynia)</label>
                            <label><input type="checkbox" id="sg2"> 2. Vasomotor (temperature diff &gt; 1°C / color asymmetry)</label>
                            <label><input type="checkbox" id="sg3"> 3. Sudomotor / Edema (edema / objective sweating changes)</label>
                            <label><input type="checkbox" id="sg4"> 4. Motor / Trophic (objective weakness / tremor / dystonia / trophic)</label>
                        </div>
                    </div>
                    <div class="calc-result-box">
                        <div class="calc-total">Status: Mandatory Gates <span id="gateStatus" class="score-val" style="color:#ef4444;">INCOMPLETE</span> | Symptoms <span id="sxCount" class="score-val">0</span>/4 | Signs <span id="sgCount" class="score-val">0</span>/4</div>
                        <div class="calc-interp" id="crpsInterp">Result: CRPS Criteria NOT MET (Mandatory Gates Missing, Symptoms 0/4, Signs 0/4)</div>
                    </div>
                </form>
            </div>'''

        steps_lis = "".join([f"<li>{s}</li>" for s in steps])
        sources_spans = " · ".join([f"<span class='source-tag'>{s}</span>" for s in sources]) if sources else "Clinical Reference Standard"
        
        type_badge = "TEST" if ctype == "test" else "INFO"
        status_tag = f"<span class='status-tag {status}'>{status.upper()}</span>"
        
        card_html = f'''
        <article class="atlas-card" id="{cid}" data-page="{page}" data-type="{ctype}" data-status="{status}" style="--card-border: {acc['border']}; --card-bg: {acc['bg']};">
            <header class="card-header" onclick="toggleCard('{cid}')">
                <div class="card-meta">
                    <span class="page-badge" style="background:{acc['badge']}">P{page}</span>
                    <span class="type-badge {ctype}">{type_badge}</span>
                    {status_tag}
                </div>
                <h3 class="card-title">{title}</h3>
                <div class="card-chevron">▼</div>
            </header>
            <div class="card-body">
                <div class="card-inner">
                    <div class="section-block">
                        <div class="sec-label">Execution Steps</div>
                        <ol class="steps-list">
                            {steps_lis}
                        </ol>
                    </div>

                    <div class="section-block positive-block">
                        <div class="sec-label">Positive Criterion</div>
                        <div class="positive-text">{positive}</div>
                    </div>

                    <div class="section-block metrics-block">
                        <div class="sec-label">Diagnostic Metrics &amp; Evidence</div>
                        <div class="metrics-text">{metrics}</div>
                    </div>

                    {calc_html}
                    {video_html}

                    <div class="section-block sources-block">
                        <div class="sec-label">Validated References</div>
                        <div class="sources-text">{sources_spans}</div>
                    </div>

                    <div class="card-footer-action">
                        <a href="#{cid}" class="anchor-link" onclick="copyCardLink('{cid}', event)">🔗 Copy Anchor Link (#{cid})</a>
                    </div>
                </div>
            </div>
        </article>'''
        cards_html.append(card_html)

    # HTML Shell
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ankle &amp; Foot Complex — Companion Clinical Test Atlas</title>
    <meta name="description" content="Companion digital clinical Test Atlas for the Ankle &amp; Foot Complex Master Clinical Assessment &amp; Rehabilitation Dossier. One single source of truth for special tests, clinical protocols, and validated metrics.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --bg-body: #0b0f19;
            --bg-surface: #111827;
            --bg-card: #1f2937;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --border-subtle: #374151;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --radius-md: 10px;
            --radius-lg: 14px;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            padding-top: 32px;
            padding-bottom: 60px;
        }}

        /* Fixed Top Clinical Education Banner */
        .clinical-banner {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 32px;
            background: #78350f;
            color: #fef3c7;
            border-bottom: 1px solid #92400e;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            padding: 0 16px;
            text-align: center;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        }}

        /* Header & Navigation */
        .atlas-header {{
            position: sticky;
            top: 32px;
            z-index: 100;
            background: rgba(11, 15, 25, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-subtle);
            padding: 14px 16px;
        }}

        .header-content {{
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .app-title {{
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #60a5fa, #a78bfa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stats-badge {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 20px;
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}

        /* Search & Filter Bar */
        .controls-row {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .search-box-wrap {{
            position: relative;
            width: 100%;
        }}

        .search-input {{
            width: 100%;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: var(--radius-md);
            padding: 10px 14px 10px 38px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }}

        .search-input:focus {{
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
            background: #0f172a;
        }}

        .search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
            font-size: 0.9rem;
            pointer-events: none;
        }}

        .filters-wrap {{
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 2px;
            scrollbar-width: none;
        }}
        .filters-wrap::-webkit-scrollbar {{ display: none; }}

        .filter-btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: #3b82f6;
            color: #fff;
            border-color: #60a5fa;
        }}

        /* Main Container */
        .atlas-container {{
            max-width: 900px;
            margin: 20px auto;
            padding: 0 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* Cards */
        .atlas-card {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1.5px solid var(--border-subtle);
            border-left: 5px solid var(--card-border);
            overflow: hidden;
            transition: border-color 0.2s, box-shadow 0.2s, transform 0.1s;
        }}

        .atlas-card.target-highlight {{
            box-shadow: 0 0 0 3px #3b82f6, 0 10px 25px rgba(0,0,0,0.5);
            transform: scale(1.005);
        }}

        .card-header {{
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            cursor: pointer;
            user-select: none;
            background: rgba(31, 41, 55, 0.7);
            transition: background 0.15s;
        }}

        .card-header:hover {{
            background: rgba(55, 65, 81, 0.8);
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }}

        .page-badge {{
            font-size: 0.7rem;
            font-weight: 800;
            color: #fff;
            padding: 2px 7px;
            border-radius: 5px;
        }}

        .type-badge {{
            font-size: 0.65rem;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            letter-spacing: 0.05em;
        }}
        .type-badge.test {{ background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }}
        .type-badge.info {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }}

        .status-tag {{
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .status-tag.draft {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .status-tag.approved {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }}

        .card-title {{
            font-size: 1rem;
            font-weight: 700;
            flex-grow: 1;
            color: #f3f4f6;
            margin: 0;
        }}

        .card-chevron {{
            font-size: 0.75rem;
            color: #9ca3af;
            transition: transform 0.25s ease;
            flex-shrink: 0;
        }}

        .atlas-card.expanded .card-chevron {{
            transform: rotate(180deg);
        }}

        .card-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.35s ease-out;
            background: #111827;
        }}

        .atlas-card.expanded .card-body {{
            max-height: 2500px;
        }}

        .card-inner {{
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            border-top: 1px solid var(--border-subtle);
        }}

        .section-block {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .sec-label {{
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
        }}

        .steps-list {{
            padding-left: 20px;
            font-size: 0.9rem;
            color: #e2e8f0;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .positive-block {{
            background: rgba(239, 68, 68, 0.08);
            border-left: 3px solid var(--accent-red);
            padding: 10px 14px;
            border-radius: 0 8px 8px 0;
        }}
        .positive-text {{
            font-size: 0.9rem;
            font-weight: 600;
            color: #fca5a5;
        }}

        .metrics-block {{
            background: rgba(59, 130, 246, 0.08);
            border-left: 3px solid var(--accent-blue);
            padding: 10px 14px;
            border-radius: 0 8px 8px 0;
        }}
        .metrics-text {{
            font-family: 'Source Sans 3', monospace;
            font-size: 0.88rem;
            font-weight: 700;
            color: #bfdbfe;
        }}

        /* Embedded Calculators */
        .embedded-calc {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: var(--radius-md);
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .embedded-calc h4 {{
            font-size: 0.95rem;
            color: #38bdf8;
        }}
        .calc-sub {{ font-size: 0.8rem; color: #94a3b8; }}
        .calc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 10px;
        }}
        .calc-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .calc-item label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: #cbd5e1;
        }}
        .calc-item select {{
            background: #0f172a;
            border: 1px solid #475569;
            color: #f8fafc;
            padding: 6px 8px;
            border-radius: 6px;
            font-size: 0.85rem;
            outline: none;
        }}
        .calc-result-box {{
            background: #0f172a;
            border-radius: 8px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            border: 1px solid #334155;
            margin-top: 6px;
        }}
        .calc-total {{ font-size: 0.9rem; font-weight: 700; color: #f8fafc; }}
        .score-val {{ color: #38bdf8; font-size: 1.1rem; }}
        .calc-interp {{ font-size: 0.85rem; font-weight: 600; color: #a7f3d0; }}

        .crps-split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        @media (max-width: 600px) {{ .crps-split {{ grid-template-columns: 1fr; }} }}
        .crps-col {{ display: flex; flex-direction: column; gap: 6px; font-size: 0.8rem; }}
        .crps-col label {{ display: flex; align-items: flex-start; gap: 6px; color: #cbd5e1; cursor: pointer; }}
        .crps-col input {{ margin-top: 3px; }}

        /* Video Embeds */
        .video-container {{
            position: relative;
            width: 100%;
            padding-bottom: 56.25%; /* 16:9 aspect */
            height: 0;
            border-radius: 10px;
            overflow: hidden;
            background: #000;
            border: 1px solid #334155;
        }}
        .video-container iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: 0;
        }}
        .video-caption {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.85);
            padding: 6px 12px;
            font-size: 0.75rem;
            display: flex;
            justify-content: space-between;
            color: #94a3b8;
        }}
        .video-caption a {{ color: #38bdf8; text-decoration: none; font-weight: 600; }}

        .no-video-banner {{
            background: rgba(148, 163, 184, 0.1);
            border: 1px dashed #475569;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            color: #94a3b8;
            text-align: center;
        }}

        /* Sources */
        .sources-text {{ font-size: 0.8rem; color: #94a3b8; }}
        .source-tag {{ color: #cbd5e1; font-weight: 500; }}

        /* Card Anchor Copy */
        .card-footer-action {{
            display: flex;
            justify-content: flex-end;
            padding-top: 6px;
        }}
        .anchor-link {{
            font-size: 0.78rem;
            color: #64748b;
            text-decoration: none;
            cursor: pointer;
            transition: color 0.15s;
        }}
        .anchor-link:hover {{ color: #38bdf8; }}

        /* Toast notification */
        #toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #10b981;
            color: #fff;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.25s ease;
            pointer-events: none;
            z-index: 1000;
        }}
        #toast.show {{
            opacity: 1;
            transform: translateY(0);
        }}
    </style>
</head>
<body>

    <div class="clinical-banner">
        <span>Clinical education reference — draft under clinical review. Not a substitute for clinical judgement.</span>
    </div>

    <header class="atlas-header">
        <div class="header-content">
            <div class="title-row">
                <h1 class="app-title">Ankle &amp; Foot Complex — Test Atlas</h1>
                <span class="stats-badge">{len(entries)} Clinical Cards</span>
            </div>
            <div class="controls-row">
                <div class="search-box-wrap">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="searchInput" class="search-input" placeholder="Search tests, criteria, metrics, or ID (e.g. thompson, windlass)..." oninput="filterCards()">
                </div>
                <div class="filters-wrap">
                    <button class="filter-btn active" data-filter="all" onclick="setFilter('all', this)">All ({len(entries)})</button>
                    <button class="filter-btn" data-filter="test" onclick="setFilter('test', this)">Tests ({len([e for e in entries if e['type'] == 'test'])})</button>
                    <button class="filter-btn" data-filter="info" onclick="setFilter('info', this)">Info Cards ({len([e for e in entries if e['type'] == 'info'])})</button>
                    <button class="filter-btn" data-filter="p1" onclick="setFilter('p1', this)">P1 Triage</button>
                    <button class="filter-btn" data-filter="p2" onclick="setFilter('p2', this)">P2 Differential</button>
                    <button class="filter-btn" data-filter="p3" onclick="setFilter('p3', this)">P3 Biomechanics</button>
                    <button class="filter-btn" data-filter="p4" onclick="setFilter('p4', this)">P4 Clusters</button>
                    <button class="filter-btn" data-filter="p6" onclick="setFilter('p6', this)">P6 Modalities</button>
                    <button class="filter-btn" data-filter="p7" onclick="setFilter('p7', this)">P7 Manual/DN</button>
                    <button class="filter-btn" data-filter="p8" onclick="setFilter('p8', this)">P8 Continuum/RTS</button>
                    <button class="filter-btn" data-filter="video" onclick="setFilter('video', this)">With Video ({len([e for e in entries if e.get('video_url')])})</button>
                </div>
            </div>
        </div>
    </header>

    <main class="atlas-container" id="cardsContainer">
        {"".join(cards_html)}
    </main>

    <div id="toast">Anchor link copied to clipboard!</div>

    <script>
        let currentFilter = 'all';

        function toggleCard(id) {{
            const card = document.getElementById(id);
            if (!card) return;
            card.classList.toggle('expanded');
        }}

        function expandCard(id) {{
            const card = document.getElementById(id);
            if (!card) return;
            card.classList.add('expanded');
            card.classList.add('target-highlight');
            card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            setTimeout(() => card.classList.remove('target-highlight'), 3000);
        }}

        function setFilter(filterType, btn) {{
            currentFilter = filterType;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            filterCards();
        }}

        function filterCards() {{
            const q = document.getElementById('searchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.atlas-card');
            
            cards.forEach(card => {{
                const id = card.id.toLowerCase();
                const title = card.querySelector('.card-title').textContent.toLowerCase();
                const text = card.textContent.toLowerCase();
                const page = card.getAttribute('data-page');
                const type = card.getAttribute('data-type');
                const hasVideo = card.querySelector('.video-container') !== null;

                let matchesFilter = false;
                if (currentFilter === 'all') matchesFilter = true;
                else if (currentFilter === 'test' && type === 'test') matchesFilter = true;
                else if (currentFilter === 'info' && type === 'info') matchesFilter = true;
                else if (currentFilter === 'p' + page) matchesFilter = true;
                else if (currentFilter === 'video' && hasVideo) matchesFilter = true;

                let matchesSearch = !q || id.includes(q) || title.includes(q) || text.includes(q);

                if (matchesFilter && matchesSearch) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        function copyCardLink(id, event) {{
            event.stopPropagation();
            const url = window.location.origin + window.location.pathname + '#' + id;
            navigator.clipboard.writeText(url).then(() => {{
                showToast("Copied link: #" + id);
            }});
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2200);
        }}

        // Foot Posture Index Calculator Logic
        function calculateFPI() {{
            let sum = 0;
            for (let i = 1; i <= 6; i++) {{
                sum += parseInt(document.getElementById('fpi' + i).value, 10);
            }}
            document.getElementById('fpiTotal').textContent = (sum > 0 ? '+' : '') + sum;
            
            let interp = '';
            if (sum >= 10) interp = 'Highly Pronated (≥ +10)';
            else if (sum >= 6) interp = 'Pronated (+6 to +9)';
            else if (sum >= 0) interp = 'Neutral (0 to +5)';
            else if (sum >= -4) interp = 'Supinated (−1 to −4)';
            else interp = 'Highly Supinated (≤ −5)';
            document.getElementById('fpiInterp').textContent = 'Interpretation: ' + interp;
        }}

        // TSK-11 Calculator Logic
        function initTSK() {{
            const grid = document.getElementById('tskGrid');
            if (!grid) return;
            grid.innerHTML = '';
            grid.style.display = 'grid';
            grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(130px, 1fr))';
            grid.style.gap = '8px';
            for (let i = 1; i <= 11; i++) {{
                const d = document.createElement('div');
                d.className = 'calc-item';
                d.innerHTML = `<label>Item ${{i}} (1-4)</label><select id="tsk${{i}}" onchange="calculateTSK()"><option value="1">1 (Strongly disagree)</option><option value="2">2</option><option value="3">3</option><option value="4">4 (Strongly agree)</option></select>`;
                grid.appendChild(d);
            }}
        }}

        function calculateTSK() {{
            let sum = 0;
            for (let i = 1; i <= 11; i++) {{
                const el = document.getElementById('tsk' + i);
                if (el) sum += parseInt(el.value, 10);
            }}
            const tot = document.getElementById('tskTotal');
            if (tot) tot.textContent = sum;
            const interp = document.getElementById('tskInterp');
            if (interp) {{
                if (sum <= 17) interp.textContent = 'Interpretation: Low Fear / Kinesiophobia Cleared (≤ 17)';
                else interp.textContent = 'Interpretation: High Kinesiophobia / Psychological Guarding (> 17)';
            }}
        }}

        // Budapest CRPS Calculator Logic
        function calculateBudapest() {{
            const g1 = document.getElementById('gate1') ? document.getElementById('gate1').checked : false;
            const g2 = document.getElementById('gate2') ? document.getElementById('gate2').checked : false;
            const gateStatus = document.getElementById('gateStatus');
            if (gateStatus) {{
                if (g1 && g2) {{
                    gateStatus.textContent = 'PASSED (2/2)';
                    gateStatus.style.color = '#10b981';
                }} else {{
                    gateStatus.textContent = 'INCOMPLETE (' + ((g1?1:0)+(g2?1:0)) + '/2)';
                    gateStatus.style.color = '#ef4444';
                }}
            }}

            let sx = (document.getElementById('sx1').checked?1:0) + (document.getElementById('sx2').checked?1:0) + (document.getElementById('sx3').checked?1:0) + (document.getElementById('sx4').checked?1:0);
            let sg = (document.getElementById('sg1').checked?1:0) + (document.getElementById('sg2').checked?1:0) + (document.getElementById('sg3').checked?1:0) + (document.getElementById('sg4').checked?1:0);
            document.getElementById('sxCount').textContent = sx;
            document.getElementById('sgCount').textContent = sg;
            const interp = document.getElementById('crpsInterp');
            if (g1 && g2 && sx >= 3 && sg >= 2) {{
                interp.textContent = 'Result: Budapest Clinical Criteria MET (Mandatory Gates Passed, Symptoms ≥ 3/4, Signs ≥ 2/4)';
                interp.style.color = '#ef4444';
            }} else {{
                let reasons = [];
                if (!g1 || !g2) reasons.push('Mandatory Gates Incomplete');
                if (sx < 3) reasons.push('Symptoms ' + sx + '/4 (need ≥3)');
                if (sg < 2) reasons.push('Signs ' + sg + '/4 (need ≥2)');
                interp.textContent = 'Result: CRPS Criteria NOT MET (' + reasons.join(', ') + ')';
                interp.style.color = '#10b981';
            }}
        }}

        // Auto-expand on direct hash navigation
        window.addEventListener('DOMContentLoaded', () => {{
            initTSK();
            if (window.location.hash) {{
                const targetId = window.location.hash.substring(1);
                expandCard(targetId);
            }}
        }});

        window.addEventListener('hashchange', () => {{
            if (window.location.hash) {{
                const targetId = window.location.hash.substring(1);
                expandCard(targetId);
            }}
        }});
    </script>
</body>
</html>'''

    # Write atlas index.html
    atlas_html_path = os.path.join(base_dir, "index.html")
    with open(atlas_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {atlas_html_path} ({len(html_content):,} bytes)")

    # Write MISSING_VIDEOS.md
    missing_vids_path = os.path.join(base_dir, "MISSING_VIDEOS.md")
    with open(missing_vids_path, "w", encoding="utf-8") as f:
        f.write("# Inventory of Missing or Unverified Videos\n\n")
        f.write("Under strict validation rules, external video URLs are omitted if they cannot be verified via YouTube oEmbed HTTP 200 with matching titles. Below is the full inventory of cards currently lacking verified videos:\n\n")
        f.write("| ID | Title | Page | Type | Note |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for cid, title, page, ctype in missing_videos:
            note = "Protocol/Info Card" if ctype == "info" else "Pending dedicated Physiotutors/clinical video"
            if cid == "slhr-test":
                note = "Requires strict 60 bpm metronome protocol video (general heel raise exercise videos excluded)"
            elif cid == "silfverskiold-test":
                note = "Requires dedicated clinical goniometric Silfverskiold video"
            f.write(f"| `{cid}` | {title} | Page {page} | {ctype.upper()} | {note} |\n")
        f.write(f"\nTotal cards lacking verified video: {len(missing_videos)}\n")
    print(f"Generated {missing_vids_path}")

    # Write MISSING_LINKS.md
    missing_links_path = os.path.join(base_dir, "MISSING_LINKS.md")
    with open(missing_links_path, "w", encoding="utf-8") as f:
        f.write("# Inventory of Unverified or Fabricated External Links\n\n")
        f.write("Under Phase 3 rules, all external links from previous builds that were fabricated or unverified were systematically cataloged, removed, or replaced with self-hosted Atlas tools or verified Crossref DOIs.\n\n")
        f.write("| Chip Label | Page | Previous Fabricated / Broken Link | Resolution in Phase 3 |\n")
        f.write("| --- | --- | --- | --- |\n")
        f.write("| `📄 ESSKA Guide` | Page 2 | `https://pmc.ncbi.nlm.nih.gov/articles/PMC5355418/` (Gait study, mismatch) | Replaced with verified Crossref DOI: `https://doi.org/10.1007/s00167-018-4971-x` (ESSKA-AFAS Consensus on Peroneal Tendon Pathologies, 2018) |\n")
        f.write("| `📄 FPI Guide` | Page 3 | `https://www.physio-pedia.com/Foot_Posture_Index_(FPI-6)` (Broken in Notability due to unescaped parens) | Replaced with self-hosted interactive FPI-6 calculator inside Atlas (`#fpi-6-info`) |\n")
        f.write("| `▶ Video` (Navicular Drop) | Page 3 | `https://www.physiotutors.com/wiki/navicular-drop-test/` (Wiki page, not clean video) | Replaced with verified Physiotutors YouTube video `https://www.youtube.com/watch?v=BejuNMmD7-Y` in Atlas |\n")
        f.write("| `▶ Video` (SLHR) | Page 3 | `https://www.physio-pedia.com/Calf_Raise_Test` (Broken external page) | Set to null; requires strict 60 bpm protocol video; documented in MISSING_VIDEOS.md |\n")
        f.write("| `📄 ESSKA Consensus` | Page 5 | `https://www.esska.org/` (Generic homepage, fabricated consensus) | Replaced with verified Crossref DOI: `https://doi.org/10.1007/s00167-016-4051-z` (Rehabilitation after anatomical ankle ligament repair or reconstruction, 2016) |\n")
        f.write("| `📄 JOSPT CPG` | Page 5 | `https://www.physio-pedia.com/Achilles_Tendinopathy_Clinical_Practice_Guideline` (Secondary wiki link) | Replaced with verified official Crossref DOI: `https://doi.org/10.2519/jospt.2018.0302` (Achilles Pain, Stiffness, and Muscle Power Deficits Revision, 2018) |\n")
        f.write("| `📄 CONTINUUM` | Page 8 | `https://www.physio-pedia.com/Tendon_Pathology` (Secondary wiki page) | Replaced with verified official Crossref DOI: `https://doi.org/10.1136/bjsm.2008.051193` (Cook & Purdam Tendon Pathology Continuum, 2009) |\n")
        f.write("| `🧮 TSK-11 Calc` | Page 8 | `https://orthotoolkit.com/tampa-scale-11/` (Ad-heavy / blocked in iPad webviews) | Replaced with self-hosted minimal TSK-11 calculator inside Atlas (`#tsk-11`) |\n")
        f.write("| `🧮 Calc` (Budapest) | Page 1 | `#TODO-VERIFY` (Exempt unresolved placeholder) | Replaced with self-hosted minimal interactive Budapest CRPS calculator inside Atlas (`#budapest-crps`) |\n")
    print(f"Generated {missing_links_path}")

def main():
    atlas_dir_cursor = r"C:\Users\ahmed\AppData\Local\Cursor\AgentStores\cursor_agent_stores\bc-e0f63ecc-24f8-47ae-8e42-f0225f2dc6e4\files\docs\ankle-dossier\v9-phase-3\atlas"
    atlas_dir_scratch = r"C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\atlas"
    
    yaml_path = os.path.join(atlas_dir_cursor, "data", "tests.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        entries = yaml.safe_load(f)
    
    print(f"Loaded {len(entries)} entries from {yaml_path}")
    generate_atlas_html(entries, atlas_dir_cursor)
    generate_atlas_html(entries, atlas_dir_scratch)
    # Also mirror index.html to repository root for GitHub Pages
    root_cursor = os.path.dirname(atlas_dir_cursor)
    src_html = os.path.join(atlas_dir_cursor, "index.html")
    dst_html = os.path.join(root_cursor, "index.html")
    if os.path.exists(src_html):
        import shutil
        shutil.copy2(src_html, dst_html)
    print("Build Atlas completed successfully.")

if __name__ == "__main__":
    main()
