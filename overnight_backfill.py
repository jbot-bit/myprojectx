# --- CONFIG ---
$ProjectDir = "C:\Users\sydne\OneDrive\myprojectx"
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$LogDir     = Join-Path $ProjectDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Backfill window: last N months ending yesterday (local)
$MonthsBack = 6

# Retries per chunk/day
$MaxRetries = 5
$RetrySleepSeconds = 20

# Optional: turn off in-backfill daily features (recommended)
$env:RUN_DAILY_FEATURES = "false"

Set-Location $ProjectDir

function Run-WithRetry([string]$Args, [string]$Tag) {
  for ($i=1; $i -le $MaxRetries; $i++) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $log = Join-Path $LogDir "$Tag`_$ts`_try$i.log"

    "=== $Tag try $i ===" | Tee-Object -FilePath $log -Append
    & $VenvPython @Args 2>&1 | Tee-Object -FilePath $log -Append
    $code = $LASTEXITCODE

    if ($code -eq 0) { return $true }

    "ExitCode=$code. Sleeping $RetrySleepSeconds s..." | Tee-Object -FilePath $log -Append
    Start-Sleep -Seconds $RetrySleepSeconds
  }
  return $false
}

# --- Compute date ranges ---
# "Yesterday" local (Australia/Brisbane on your script)
$yesterday = (Get-Date).Date.AddDays(-1)

# Clamp end date to yesterday (prevents requesting "today" when provider lags)
$end = $yesterday

# Build month chunks backwards
for ($m=0; $m -lt $MonthsBack; $m++) {
  $chunkEnd   = $end.AddDays(- (30 * $m))
  $chunkStart = $chunkEnd.AddDays(-29)

  $s = $chunkStart.ToString("yyyy-MM-dd")
  $e = $chunkEnd.ToString("yyyy-MM-dd")

  $tag = "backfill_$s`_to_$e"
  $ok = Run-WithRetry @("backfill_databento_range.py", $s, $e) $tag
  if (-not $ok) {
    Write-Host "FAILED chunk $s -> $e" -ForegroundColor Red
    exit 1
  }
}

# --- Build daily_features for the same window (per-day, resumable) ---
# If your build_daily_features.py takes ONE date arg (per your earlier logs), do per-day:
$startAll = $yesterday.AddDays(- (30*$MonthsBack) + 1)

for ($d = $startAll; $d -le $yesterday; $d = $d.AddDays(1)) {
  $ds = $d.ToString("yyyy-MM-dd")
  $tag = "features_$ds"
  $ok = Run-WithRetry @("build_daily_features.py", $ds) $tag
  if (-not $ok) {
    Write-Host "FAILED daily_features $ds" -ForegroundColor Red
    exit 1
  }
}

# --- Quick sanity (counts) ---
& $VenvPython -c "import duckdb; con=duckdb.connect('gold.db'); print('bars_1m', con.execute('select count(*) from bars_1m').fetchone()[0]); print('daily_features', con.execute('select count(*) from daily_features').fetchone()[0]); con.close()"
