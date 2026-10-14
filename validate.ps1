param(
  [string]$Src = "C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\master_ankle_dossier.html",
  [string]$Pdf = "C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\master_ankle_dossier.pdf"
)
$ErrorActionPreference = "Continue"
$scratch = Split-Path $MyInvocation.MyCommand.Path
$localHtml = Join-Path $scratch "master_ankle_dossier.html"
if (-not $PSBoundParameters.ContainsKey("Src") -and (Test-Path $localHtml)) { $Src = $localHtml }
if (-not $PSBoundParameters.ContainsKey("Pdf")) { $Pdf = Join-Path $scratch "master_ankle_dossier.pdf" }
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$profile = Join-Path $env:TEMP "edgeprobe"

# ---------- 1. Raw non-ASCII scan ----------
$raw = [System.IO.File]::ReadAllText($Src, [System.Text.Encoding]::UTF8)
$bad = @()
$lines = $raw -split "`n"
for ($i = 0; $i -lt $lines.Count; $i++) {
  foreach ($ch in $lines[$i].ToCharArray()) { if ([int]$ch -gt 127) { $bad += "L$($i+1): U+{0:X4} '$ch'" -f [int]$ch; break } }
}
"=== NON-ASCII CHARACTERS: $($bad.Count) lines ==="
$bad | Select-Object -First 15

# ---------- 2. Layout measurement ----------
$probe = @'
<script>
window.addEventListener("load",()=>setTimeout(()=>{
  const PX=3.7795275591; const mm=v=>(v/PX).toFixed(1); let out=[];
  document.querySelectorAll(".clinical-page").forEach(p=>{
    const pr=p.getBoundingClientRect(); const cs=getComputedStyle(p);
    const innerRight=pr.right-parseFloat(cs.paddingRight)+1;
    let hOver=[]; p.querySelectorAll("*").forEach(e=>{ if(e.closest("svg")&&e.tagName!=="svg")return; const r=e.getBoundingClientRect(); if(r.width>0&&r.right>innerRight){hOver.push((e.id||e.className||e.tagName).toString().slice(0,28)+"@"+mm(r.right-innerRight))} });
    p.querySelectorAll(".fill").forEach(f=>{f.style.flex="0 0 auto";});
    p.style.height="auto"; p.style.maxHeight="none";
    const nat=p.scrollHeight; const content=nat/PX-14;
    out.push(p.id+" | page natural "+mm(nat)+" mm / 297 | content "+content.toFixed(1)+" mm / 283 | slack "+(283-content).toFixed(1)+" mm | "+(content<=283?"OK":"OVERFLOW")+" | hOverflow "+hOver.length+(hOver.length?" ["+hOver.slice(0,4).join(", ")+"]":""));
  });
  const fontOk=document.fonts.check("700 9px Inter");
  out.push("Inter loaded: "+fontOk+" | links: "+document.querySelectorAll("a[href]").length);
  const d=document.createElement("pre"); d.id="RESULT"; d.textContent=out.join("\n"); document.body.appendChild(d);
},3000));
</script></body>
'@
$measure = Join-Path $scratch "measure.html"
[System.IO.File]::WriteAllText($measure, ($raw -replace '</body>', $probe), (New-Object System.Text.UTF8Encoding $false))
$dom = Join-Path $scratch "dom.html"
Start-Process -FilePath $edge -ArgumentList @("--headless=new","--disable-gpu","--user-data-dir=$profile","--window-size=1400,2000","--virtual-time-budget=20000","--dump-dom","file:///$($measure -replace '\\','/')") -RedirectStandardOutput $dom -RedirectStandardError (Join-Path $scratch "err.txt") -Wait -NoNewWindow
$c = [System.IO.File]::ReadAllText($dom)
"=== LAYOUT ==="
if ($c -match '(?s)<pre id="RESULT">(.*?)</pre>') { $Matches[1] -replace '&amp;','&' } else { "no result" }

# ---------- 3. PDF export ----------
if (Test-Path $Pdf) { Remove-Item $Pdf -Force }
Start-Process -FilePath $edge -ArgumentList @("--headless=new","--disable-gpu","--user-data-dir=$profile","--no-pdf-header-footer","--virtual-time-budget=20000","--print-to-pdf=$Pdf","file:///$($Src -replace '\\','/')") -RedirectStandardError (Join-Path $scratch "err2.txt") -Wait -NoNewWindow
$bytes = [System.IO.File]::ReadAllBytes($Pdf)
$txt = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
"=== PDF ==="
"Size: {0:N0} bytes" -f $bytes.Length
"Pages: " + ([regex]::Matches($txt, '/Type\s*/Page(?![s\w])')).Count
$uri = [regex]::Matches($txt, '/URI\s*\(([^)]*)\)')
"External URI links: " + $uri.Count
"Internal GoTo links: " + ([regex]::Matches($txt, '/S\s*/GoTo|/Dest\s*[\[/(]')).Count
$rects = [regex]::Matches($txt, '/Subtype\s*/Link[^>]*?/Rect\s*\[\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)')
if ($rects.Count -eq 0) { $rects = [regex]::Matches($txt, '/Rect\s*\[\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s*\]') }
$sizes = $rects | ForEach-Object { $w=[double]$_.Groups[3].Value-[double]$_.Groups[1].Value; $h=[double]$_.Groups[4].Value-[double]$_.Groups[2].Value; [pscustomobject]@{W=[math]::Round($w,1);H=[math]::Round($h,1)} }
if ($sizes) { "Link rects: n=$($sizes.Count) | min W {0} pt | min H {1} pt (44 CSS px = 33 pt)" -f ($sizes.W | Measure-Object -Minimum).Minimum, ($sizes.H | Measure-Object -Minimum).Minimum }
$uri | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique

# Hard-fail: collisions, required strings, page count, card bounds, link targets
$checker = Join-Path $scratch "tools\check_dossier.py"
$cards = Join-Path $scratch "tools\check_cards.py"
if (-not (Test-Path $checker)) { Write-Error "Missing tools\check_dossier.py. If pdfplumber is missing: pip install pdfplumber pypdf"; exit 2 }
if (-not (Test-Path $cards)) { Write-Error "Missing tools\check_cards.py"; exit 2 }
python $checker $Pdf $Src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python $cards $Src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
