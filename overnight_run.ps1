$ProjectDir = "C:\Users\sydne\OneDrive\myprojectx"
$Py         = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$LogDir     = Join-Path $ProjectDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectDir

$env:RUN_DAILY_FEATURES = "false"

$End   = (Get-Date).Date.AddDays(-1)
$Start = $End.AddDays(-29)

function RunRetry([string[]]$args, [string]$tag, [int]$max=20, [int]$sleep=30) {
  for ($i=1; $i -le $max; $i++) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $log = Join-Path $LogDir "$tag`_$ts`_try$i.log"
    "=== $tag try $i ===" | Tee-Object -FilePath $log -Append
    & $Py @args 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -eq 0) { return $true }
    "ExitCode=$LASTEXITCODE. Sleeping $sleep s..." | Tee-Object -FilePath $log -Append
    Start-Sleep -Seconds $sleep
  }
  return $false
}

$startStr = $Start.ToString("yyyy-MM-dd")
$endStr   = $End.ToString("yyyy-MM-dd")

$ok = RunRetry @("backfill_databento_range.py", $startStr, $endStr) "backfill_$startStr`_to_$endStr"
if (-not $ok) { Write-Host "FAILED raw backfill" -ForegroundColor Red; exit 1 }

for ($d = $Start; $d -le $End; $d = $d.AddDays(1)) {
  $ds = $d.ToString("yyyy-MM-dd")
  $ok = RunRetry @("build_daily_features.py", $ds) "features_$ds" 10 20
  if (-not $ok) { Write-Host "FAILED daily_features $ds" -ForegroundColor Red; exit 1 }
}

& $Py -c "import duckdb; con=duckdb.connect('gold.db'); print('bars_1m', con.execute('select count(*) from bars_1m').fetchone()[0]); print('daily_features', con.execute('select count(*) from daily_features').fetchone()[0]); con.close()"
Write-Host "DONE" -ForegroundColor Green
