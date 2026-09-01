Set-Location C:\kite-agent\brain
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$out   = "70-ops\status\repo-manifest-$stamp.md"
New-Item -ItemType Directory -Force -Path "70-ops\status" | Out-Null

# PATCH (ledger V12): capture into variables joined by newlines first.
$gitStatus = (git status 2>&1)           -join "`n"
$gitLog    = (git log --oneline -5 2>&1) -join "`n"

$L = New-Object System.Collections.Generic.List[string]
$L.Add("# REPO MANIFEST - $stamp")
$L.Add("")
$L.Add("## GIT STATUS")
$L.Add('```'); $L.Add($gitStatus); $L.Add('```')
$L.Add("")
$L.Add("## GIT LOG (5)")
$L.Add('```'); $L.Add($gitLog); $L.Add('```')
$L.Add("")
$L.Add("## FILE COUNTS")
foreach ($p in @("60-tools\python,*.py", "60-tools\powershell,*.ps1",
                 "90-scripts,*.py", "20-market-data\datasets,*.csv",
                 "70-ops\status,*", "01_PLAN,*.md")) {
    $parts = $p -split ","
    $n = (Get-ChildItem -Path $parts[0] -Filter $parts[1] -File -ErrorAction SilentlyContinue |
          Measure-Object).Count
    $L.Add("- $($parts[0]) ($($parts[1])): $n")
}
$L.Add("")
$L.Add("## CRITICAL FILES")
foreach ($f in @("20-market-data\datasets\instruments-2026-08-31.csv",
                 "20-market-data\datasets\dhan-scrip-master-2026-08-31.csv",
                 "60-tools\python\bridge_structured_join.py",
                 "90-scripts\b0_probe.py",
                 "01_PLAN\00_CONVENTIONS.md",
                 "01_PLAN\00_CORRECTIONS_LEDGER.md",
                 "01_PLAN\PHASE_B_bridge.md")) {
    $L.Add("- $f : $(if (Test-Path $f) { 'EXISTS' } else { 'MISSING' })")
}
$L.Add("")
$L.Add("## SECRETS (existence only, never contents)")
foreach ($s in @("dhan.env", "kite.env", "kite_token.json")) {
    $fp = "C:\kite-agent\secrets\$s"
    $L.Add("- $s : $(if (Test-Path $fp) { 'EXISTS' } else { 'MISSING' })")
}
$L.Add("")
$L.Add("## WRITE SCRIPT INVENTORY")
$w = Get-ChildItem -Path "60-tools\powershell" -Filter "write*.ps1" -File -ErrorAction SilentlyContinue |
     Select-Object -ExpandProperty Name | Sort-Object
if ($w) { foreach ($x in $w) { $L.Add("- $x") } } else { $L.Add("- (none)") }

$L | Out-File -FilePath $out -Encoding utf8
Write-Host "manifest: $out"
Get-Content $out
