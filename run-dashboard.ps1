$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw 'Create .venv and install requirements.txt first; see README.md.'
    }
    & $pythonExe -m src.cli import-manual
    if ($LASTEXITCODE -ne 0) { throw 'Manual evidence import failed.' }
    & $pythonExe -m streamlit run app/dashboard.py --server.address 127.0.0.1
} finally {
    Pop-Location
}
