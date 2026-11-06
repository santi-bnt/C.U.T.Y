$ErrorActionPreference = "Stop"
$cutyRaspberry = Split-Path -Parent $PSScriptRoot
Push-Location $cutyRaspberry
try {
    if (-not (Test-Path -LiteralPath ".venv/Scripts/python.exe")) {
        py -3 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
    }
    & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    Write-Output "Ready. From raspberry/, run .\.venv\Scripts\python.exe -m cuty."
} finally {
    Pop-Location
}
