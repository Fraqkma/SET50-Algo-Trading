$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$archive = Join-Path $repo 'tradeSim0.2.5.zip'
$runtime = Join-Path $repo 'tools\kgi_tradesim'
$venv = Join-Path $repo '.venv-kgi313'
if (-not (Test-Path -LiteralPath $archive)) { throw "Local TradeSim 0.2.5 archive not found: $archive" }
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { throw 'Python launcher (py) was not found; exact Python 3.13.0 is required.' }
$probe = & $py.Source -3.13 -c "import sys; print(sys.executable); print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0 -or $probe[-1] -ne '3.13.0') {
    throw "Python 3.13.0 is required exactly. Launcher reported: $($probe -join ', ')"
}
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'TradingSimulation.ipynb'))) {
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    Expand-Archive -LiteralPath $archive -DestinationPath $runtime -Force
}
& $probe[0] -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv-kgi313.' }
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install -r (Join-Path $runtime 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'TradeSim requirements installation failed.' }
& $python -c "import sys,tradeSim; print(sys.version); print('TradeSim import OK:', tradeSim.__file__)"
if ($LASTEXITCODE -ne 0) { throw 'TradeSim import check failed.' }
