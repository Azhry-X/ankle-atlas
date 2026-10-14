$ErrorActionPreference = "Stop"
$src = "C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\master_ankle_dossier.html"
$pdf = "C:\Users\ahmed\.gemini\antigravity-ide\scratch\ankle_dossier\master_ankle_dossier_GOLDEN.pdf"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$localHtml = Join-Path $here "master_ankle_dossier.html"
if (Test-Path $localHtml) {
    $src = $localHtml
    $pdf = Join-Path $here "master_ankle_dossier_GOLDEN.pdf"
}
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 1. Check & ensure UTF-8 without BOM
$bytes = [System.IO.File]::ReadAllBytes($src)
$hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
Write-Host "UTF-8 BOM present: $hasBom"

if ($hasBom) {
    $text = [System.IO.File]::ReadAllText($src, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($src, $text, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "Stripped BOM successfully."
} else {
    Write-Host "File is already clean UTF-8 without BOM."
}

# 2. Compile to PDF via Edge headless
if (Test-Path $pdf) { Remove-Item $pdf -Force }
Start-Process -FilePath $edge -ArgumentList @(
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--virtual-time-budget=20000",
    "--print-to-pdf=$pdf",
    "file:///$($src -replace '\\','/')"
) -Wait -NoNewWindow

# 3. Verify PDF Page Count
if (Test-Path $pdf) {
    $pdfBytes = [System.IO.File]::ReadAllBytes($pdf)
    $pdfTxt = [System.Text.Encoding]::GetEncoding(28591).GetString($pdfBytes)
    $pageMatches = [regex]::Matches($pdfTxt, '/Type\s*/Page(?![s\w])')
    Write-Host "Compiled PDF Size: $($pdfBytes.Length) bytes"
    Write-Host "Total Pages: $($pageMatches.Count)"

    # Mirror to Desktop
    $desktop = [Environment]::GetFolderPath('Desktop')
    $desktopPdf = Join-Path $desktop "master_ankle_dossier_GOLDEN.pdf"
    Copy-Item $pdf $desktopPdf -Force
    Write-Host "Mirrored to Desktop: $desktopPdf"
    
    # Also check OneDrive desktop if different
    $oneDriveDesktop = "C:\Users\ahmed\OneDrive\Desktop\master_ankle_dossier_GOLDEN.pdf"
    if (Test-Path (Split-Path $oneDriveDesktop)) {
        Copy-Item $pdf $oneDriveDesktop -Force
        Write-Host "Mirrored to OneDrive Desktop: $oneDriveDesktop"
    }

    # Hard-fail: collisions, required strings, page count, card bounds, link targets
    $root = Split-Path -Parent $MyInvocation.MyCommand.Path
    $checker = Join-Path $root "tools\check_dossier.py"
    $cards = Join-Path $root "tools\check_cards.py"
    $routerCheck = Join-Path $root "tools\check_router_border.py"
    if (-not (Test-Path $checker)) { throw "Missing tools\check_dossier.py" }
    if (-not (Test-Path $cards)) { throw "Missing tools\check_cards.py" }
    if (-not (Test-Path $routerCheck)) { throw "Missing tools\check_router_border.py" }
    python $checker $pdf $src
    if ($LASTEXITCODE -ne 0) { throw "check_dossier.py failed with exit $LASTEXITCODE. If the error says pdfplumber is missing: pip install pdfplumber pypdf" }
    python $cards $src
    if ($LASTEXITCODE -ne 0) { throw "check_cards.py failed with exit $LASTEXITCODE" }
    python $routerCheck
    if ($LASTEXITCODE -ne 0) { throw "check_router_border.py failed with exit $LASTEXITCODE" }
} else {
    Write-Host "Error: PDF was not generated."
}
