$ErrorActionPreference = "Stop"
$cutyRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Push-Location $cutyRoot
try {
    if (-not (Test-Path -LiteralPath ".venv/Scripts/python.exe")) {
        py -3 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
    }
    & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    Write-Output "Ready. Run .\.venv\Scripts\python.exe -m cuty from the repository root."
} finally {
    Pop-Location
}
